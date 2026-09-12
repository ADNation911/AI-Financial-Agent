import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import re

from data_loader import DataLoader
from message_parser import parse_all_messages

class FinancialForecaster:
    def __init__(self, data_loader):
        self.dl = data_loader
        (self.user_salaries, 
         self.unconfirmed_gig_users, 
         self.ended_employment_users, 
         self.rent_increase_users, 
         self.childcare_users, 
         self.event_overrides) = parse_all_messages(self.dl.messages_path)
        
        with open('code/extracted_image_amounts.json', 'r', encoding='utf-8') as f:
            self.image_amounts = json.load(f)

    def convert_amount(self, amount, from_curr, to_curr, date_str):
        if from_curr == to_curr or amount == 0 or pd.isnull(amount):
            return amount if pd.notnull(amount) else 0.0
        return self.dl.get_exchange_rate(amount, from_curr, to_curr, date_str)

    def resolve_event_amount(self, event_row):
        event_id = str(event_row['event_id'])
        if event_id in self.event_overrides and self.event_overrides[event_id]['new_amount'] is not None:
            return float(self.event_overrides[event_id]['new_amount'])
        if pd.notnull(event_row['amount']):
            return float(event_row['amount'])
        if event_id in self.image_amounts and self.image_amounts[event_id] is not None:
            return float(self.image_amounts[event_id])
        return 0.0

    def is_event_cancelled(self, event_row):
        event_id = str(event_row['event_id'])
        if event_id in self.event_overrides and self.event_overrides[event_id]['cancelled']:
            return True
        status = str(event_row['status']).lower()
        if status in ['failed', 'cancelled', 'unrealized']:
            return True
        return False

    def detect_recurring_items(self, user_id):
        events_df = self.dl.get_user_events(user_id)
        valid_events = events_df[~events_df.apply(self.is_event_cancelled, axis=1)].copy()
        
        valid_events['parsed_date'] = pd.to_datetime(valid_events['event_date'])
        valid_events['resolved_amt'] = valid_events.apply(self.resolve_event_amount, axis=1)

        recurring_patterns = []
        for (category, direction), group in valid_events.groupby(['category', 'direction']):
            group = group.sort_values('parsed_date')
            if len(group) < 2:
                continue

            # Ended employment check for salary
            if category == 'salary' and user_id in self.ended_employment_users and direction == 'credit':
                continue

            # Unconfirmed gig payouts check
            if user_id in self.unconfirmed_gig_users and direction == 'credit':
                desc_lower = group['description'].str.lower().str.cat(sep=' ')
                if any(g in desc_lower for g in ['quickcrew', 'taskloop', 'ridegrid', 'workdash', 'shiftpay', 'tasksprint', 'app earnings', 'marketplace payout', 'platform payout', 'payout']):
                    continue

            # For salary credits, separate recurring payroll from one-time bonuses/arrears/commissions
            if category == 'salary' and direction == 'credit':
                desc_lower = group['description'].str.lower()
                payroll_mask = desc_lower.str.contains('payroll|base salary|net salary|monthly salary', na=False)
                commission_mask = desc_lower.str.contains('commission|bonus|arrears|performance|sales', na=False)
                platform_mask = desc_lower.str.contains('platform|marketplace|app earnings|driver|delivery|payout|weekly', na=False)
                
                if payroll_mask.sum() >= 2:
                    group = group[payroll_mask].copy()
                elif platform_mask.sum() >= 2:
                    group = group[platform_mask].copy()
                elif commission_mask.sum() > 0 and (~commission_mask).sum() >= 2:
                    group = group[~commission_mask].copy()
                
                if len(group) < 2:
                    continue
                
            group['days_diff'] = group['parsed_date'].diff().dt.days
            median_gap = group['days_diff'].median()
            
            latest_row = group.iloc[-1]
            latest_amt = latest_row['resolved_amt']
            median_amt = group['resolved_amt'].median()
            
            # Use median amount to avoid single arrears/bonus spikes
            proj_amt = median_amt if (category == 'salary' and len(group) > 2) else latest_amt
            if category != 'salary':
                proj_amt = median_amt

            # Rent increase check
            if category == 'rent' and direction == 'debit' and user_id in self.rent_increase_users:
                proj_amt = proj_amt * 1.12

            last_date = latest_row['parsed_date'].date()
            
            is_final_salary = (category == 'salary' and 'final' in str(latest_row['description']).lower())
            if is_final_salary:
                continue

            if pd.notnull(median_gap) and 5 <= median_gap <= 35 and proj_amt > 0:
                day_of_month = int(group['parsed_date'].dt.day.median())
                sample_row = group.iloc[-1]
                recurring_patterns.append({
                    'category': category,
                    'direction': direction,
                    'median_gap': median_gap,
                    'median_amt': proj_amt,
                    'day_of_month': day_of_month,
                    'currency': sample_row['currency'],
                    'flexibility': sample_row['flexibility'],
                    'sample_event_id': sample_row['event_id'],
                    'description': sample_row['description'],
                    'last_date': last_date
                })
        return recurring_patterns

    def build_user_events_timeline(self, user_id, start_date_str, days=90, spending_changes=None):
        if spending_changes is None:
            spending_changes = {}

        profile = self.dl.get_user_profile(user_id)
        home_curr = profile['home_currency']
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = start_date + timedelta(days=days)
        
        daily_inflows = {start_date + timedelta(days=i): 0.0 for i in range(days + 1)}
        daily_outflows = {start_date + timedelta(days=i): 0.0 for i in range(days + 1)}
        
        events_df = self.dl.get_user_events(user_id)
        settled_linked_ids = set(events_df[events_df['status'] == 'settled']['linked_event_id'].dropna().astype(str))

        salary_update = None
        if user_id in self.user_salaries and len(self.user_salaries[user_id]) > 0:
            salary_update = sorted(self.user_salaries[user_id], key=lambda x: x['effective_date'])[-1]

        explicit_months_by_cat = set()

        # 1. Process explicit future single events & scheduled pending transactions
        for idx, row in events_df.iterrows():
            event_id = str(row['event_id'])
            if event_id in settled_linked_ids or self.is_event_cancelled(row):
                continue
                
            status = str(row['status']).lower()
            direction = str(row['direction']).lower()
            category = str(row['category']).lower() if pd.notnull(row['category']) else ''
            
            if status == 'pending' and direction == 'credit':
                desc_lower = str(row['description']).lower() if pd.notnull(row['description']) else ''
                if user_id in self.unconfirmed_gig_users or any(g in desc_lower for g in ['quickcrew', 'taskloop', 'ridegrid', 'workdash', 'shiftpay', 'tasksprint', 'pending payout', 'unconfirmed']):
                    continue

            e_date_str = str(row['settlement_date']) if pd.notnull(row['settlement_date']) else str(row['event_date'])
            try:
                e_date = datetime.strptime(e_date_str[:10], '%Y-%m-%d').date()
            except ValueError:
                continue

            if e_date > start_date and e_date <= end_date:
                explicit_months_by_cat.add((category, direction, e_date.year, e_date.month))
                amt = self.resolve_event_amount(row)
                if category == 'salary' and salary_update is not None:
                    eff_d = datetime.strptime(salary_update['effective_date'], '%Y-%m-%d').date()
                    if e_date >= eff_d:
                        amt = salary_update['new_salary']

                # Rent increase
                if category == 'rent' and direction == 'debit' and user_id in self.rent_increase_users:
                    amt = amt * 1.12

                amt_home = self.convert_amount(amt, row['currency'], home_curr, e_date_str[:10])
                
                if event_id in spending_changes:
                    change_type, new_val = spending_changes[event_id]
                    if change_type == 'stop':
                        amt_home = 0.0
                    elif change_type == 'reduce_to':
                        amt_home = self.convert_amount(new_val, row['currency'], home_curr, e_date_str[:10])

                if direction == 'credit':
                    daily_inflows[e_date] += amt_home
                elif direction == 'debit':
                    daily_outflows[e_date] += amt_home

        # 2. Auto-project recurring patterns for future months if no explicit event exists for that month
        patterns = self.detect_recurring_items(user_id)
        for p in patterns:
            cat = p['category']
            direction = p['direction']
            sample_ev_id = str(p['sample_event_id'])
            
            if sample_ev_id in spending_changes and spending_changes[sample_ev_id][0] == 'stop':
                continue

            # Monthly patterns (~25-35 days)
            if 25 <= p['median_gap'] <= 35:
                curr_y = start_date.year
                curr_m = start_date.month
                
                for month_offset in range(0, 4):
                    m = curr_m + month_offset
                    y = curr_y + (m - 1) // 12
                    m = ((m - 1) % 12) + 1
                    
                    if (cat, direction, y, m) in explicit_months_by_cat:
                        continue
                        
                    dom = min(p['day_of_month'], 28)
                    try:
                        proj_date = datetime(y, m, dom).date()
                    except ValueError:
                        continue
                        
                    if proj_date >= start_date and proj_date <= end_date:
                        amt = p['median_amt']
                        if cat == 'salary' and salary_update is not None:
                            eff_d = datetime.strptime(salary_update['effective_date'], '%Y-%m-%d').date()
                            if proj_date >= eff_d:
                                amt = salary_update['new_salary']
                                
                        amt_home = self.convert_amount(amt, p['currency'], home_curr, proj_date.strftime('%Y-%m-%d'))
                        
                        if sample_ev_id in spending_changes and spending_changes[sample_ev_id][0] == 'reduce_to':
                            amt_home = self.convert_amount(spending_changes[sample_ev_id][1], p['currency'], home_curr, proj_date.strftime('%Y-%m-%d'))
                            
                        if direction == 'credit':
                            daily_inflows[proj_date] += amt_home
                        elif direction == 'debit':
                            daily_outflows[proj_date] += amt_home

            # Periodic patterns (5-16 days) - continue from last historical event date!
            elif 5 <= p['median_gap'] <= 16:
                gap = int(round(p['median_gap']))
                last_d = p['last_date']
                proj_date = last_d + timedelta(days=gap)
                while proj_date <= end_date:
                    if proj_date >= start_date:
                        amt_home = self.convert_amount(p['median_amt'], p['currency'], home_curr, proj_date.strftime('%Y-%m-%d'))
                        if direction == 'credit':
                            daily_inflows[proj_date] += amt_home
                        elif direction == 'debit':
                            daily_outflows[proj_date] += amt_home
                    proj_date += timedelta(days=gap)

        return daily_inflows, daily_outflows

    def simulate_balance_timeline(self, user_id, start_date_str, payment_plan_items=None, spending_changes=None):
        if payment_plan_items is None:
            payment_plan_items = []
            
        profile = self.dl.get_user_profile(user_id)
        start_bal = float(profile['current_available_balance'])
        
        inflows, outflows = self.build_user_events_timeline(user_id, start_date_str, days=90, spending_changes=spending_changes)
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        
        plan_payments_by_date = {}
        for p_date, p_amt in payment_plan_items:
            plan_payments_by_date[p_date] = plan_payments_by_date.get(p_date, 0.0) + p_amt
            
        daily_balances = {}
        curr_bal = start_bal
        min_bal_recorded = start_bal
        
        for i in range(91):
            d = start_date + timedelta(days=i)
            if i > 0:
                curr_bal += inflows.get(d, 0.0) - outflows.get(d, 0.0)
            curr_bal -= plan_payments_by_date.get(d, 0.0)
            daily_balances[d] = curr_bal
            if curr_bal < min_bal_recorded:
                min_bal_recorded = curr_bal
                
        return min_bal_recorded, daily_balances

    def calculate_amount_safe_to_pay(self, user_id, request_date_str, requested_amount, spending_changes=None):
        profile = self.dl.get_user_profile(user_id)
        min_bal_req = float(profile['minimum_balance_to_keep'])
        min_bal_recorded, daily_bals = self.simulate_balance_timeline(user_id, request_date_str, payment_plan_items=[], spending_changes=spending_changes)
        headroom = min_bal_recorded - min_bal_req
        if headroom <= 0:
            return 0.0
        return float(min(requested_amount, max(0.0, headroom)))

    def calculate_earliest_date_for_full_payment(self, user_id, request_date_str, requested_amount, spending_changes=None):
        start_date = datetime.strptime(request_date_str, '%Y-%m-%d').date()
        profile = self.dl.get_user_profile(user_id)
        min_bal_req = float(profile['minimum_balance_to_keep'])
        
        inflows, _ = self.build_user_events_timeline(user_id, request_date_str, days=90, spending_changes=spending_changes)
        candidate_dates = [start_date] + [d for d, inf in inflows.items() if inf > 0]
        candidate_dates.sort()
        
        for eval_date in candidate_dates:
            min_bal, _ = self.simulate_balance_timeline(
                user_id, request_date_str, 
                payment_plan_items=[(eval_date, requested_amount)], 
                spending_changes=spending_changes
            )
            if min_bal >= min_bal_req:
                return eval_date.strftime('%Y-%m-%d')
                
        return ""

    def find_spending_changes_needed(self, user_id, request_date_str, requested_amount):
        profile = self.dl.get_user_profile(user_id)
        reducible_cats = [c.strip().lower() for c in str(profile['expense_categories_user_is_willing_to_reduce']).split('|')] if pd.notnull(profile['expense_categories_user_is_willing_to_reduce']) else []
        stoppable_cats = [c.strip().lower() for c in str(profile['expense_categories_user_is_willing_to_stop']).split('|')] if pd.notnull(profile['expense_categories_user_is_willing_to_stop']) else []
        
        events_df = self.dl.get_user_events(user_id)
        
        flexible_events = []
        for idx, row in events_df.iterrows():
            if str(row['flexibility']).lower() in ['flexible', 'stoppable', 'reducible', 'reducible_or_stoppable'] and str(row['direction']).lower() == 'debit':
                cat = str(row['category']).lower() if pd.notnull(row['category']) else ''
                ev_id = str(row['event_id'])
                min_allowed = float(row['minimum_allowed_amount']) if pd.notnull(row['minimum_allowed_amount']) else None
                flexible_events.append({
                    'event_id': ev_id,
                    'category': cat,
                    'description': str(row['description']),
                    'amount': self.resolve_event_amount(row),
                    'min_allowed': min_allowed,
                    'can_stop': cat in stoppable_cats,
                    'can_reduce': cat in reducible_cats and min_allowed is not None
                })

        for fe in flexible_events:
            if fe['can_stop']:
                changes = {fe['event_id']: ('stop', 0.0)}
                changes_str = f"stop:{fe['event_id']}"
                amt_safe = self.calculate_amount_safe_to_pay(user_id, request_date_str, requested_amount, spending_changes=changes)
                if amt_safe >= requested_amount:
                    return changes, changes_str, fe['description']

        for fe in flexible_events:
            if fe['can_reduce']:
                changes = {fe['event_id']: ('reduce_to', fe['min_allowed'])}
                changes_str = f"reduce_to:{fe['event_id']}:{fe['min_allowed']:g}"
                amt_safe = self.calculate_amount_safe_to_pay(user_id, request_date_str, requested_amount, spending_changes=changes)
                if amt_safe >= requested_amount:
                    return changes, changes_str, fe['description']

        for fe1 in flexible_events:
            for fe2 in flexible_events:
                if fe1['event_id'] != fe2['event_id']:
                    if fe1['can_stop'] and fe2['can_reduce']:
                        changes = {
                            fe1['event_id']: ('stop', 0.0),
                            fe2['event_id']: ('reduce_to', fe2['min_allowed'])
                        }
                        changes_str = f"stop:{fe1['event_id']}|reduce_to:{fe2['event_id']}:{fe2['min_allowed']:g}"
                        amt_safe = self.calculate_amount_safe_to_pay(user_id, request_date_str, requested_amount, spending_changes=changes)
                        if amt_safe >= requested_amount:
                            return changes, changes_str, f"{fe1['description']} and {fe2['description']}"

        return None, "none", ""

    def evaluate_request(self, request_row):
        req_id = request_row['request_id']
        user_id = request_row['user_id']
        req_date_str = request_row['request_date']
        req_amt = float(request_row['requested_amount'])
        desired_comp_str = request_row['desired_completion_date']
        allows_partial = str(request_row['allows_partial_payment']).lower() == 'true'
        
        profile = self.dl.get_user_profile(user_id)
        considered_methods = [m.strip() for m in str(profile['payment_methods_user_will_consider']).split('|')]
        max_inst_months = float(profile['max_installment_months']) if pd.notnull(profile['max_installment_months']) else 0
        min_bal_req = float(profile['minimum_balance_to_keep'])
        curr = profile['home_currency']
        
        req_date_obj = datetime.strptime(req_date_str, '%Y-%m-%d').date()
        desired_comp_obj = datetime.strptime(desired_comp_str, '%Y-%m-%d').date()

        amount_safe = self.calculate_amount_safe_to_pay(user_id, req_date_str, req_amt, spending_changes=None)
        earliest_full_date = self.calculate_earliest_date_for_full_payment(user_id, req_date_str, req_amt, spending_changes=None)

        candidate_plans = []

        # Option A: full_payment
        if 'full_payment' in considered_methods and amount_safe >= req_amt:
            candidate_plans.append({
                'affordability_status': 'affordable_now',
                'recommended_payment_method': 'full_payment',
                'payment_plan': f"{req_date_str}:{self.format_amt(req_amt)}",
                'earliest_date_for_full_payment': req_date_str,
                'spending_changes_needed': 'none',
                'total_cost': req_amt,
                'num_payments': 1,
                'start_date': req_date_str,
                'completes_by_deadline': True,
                'requires_spending_changes': False,
                'option_id': '0_full',
                'method_rank': 1
            })

        # Option B: partial_payment
        if 'partial_payment' in considered_methods and allows_partial and 0 < amount_safe < req_amt:
            if earliest_full_date and datetime.strptime(earliest_full_date, '%Y-%m-%d').date() <= desired_comp_obj:
                second_amt = req_amt - amount_safe
                candidate_plans.append({
                    'affordability_status': 'affordable_with_plan',
                    'recommended_payment_method': 'partial_payment',
                    'payment_plan': f"{req_date_str}:{self.format_amt(amount_safe)}|{earliest_full_date}:{self.format_amt(second_amt)}",
                    'earliest_date_for_full_payment': earliest_full_date,
                    'spending_changes_needed': 'none',
                    'total_cost': req_amt,
                    'num_payments': 2,
                    'start_date': req_date_str,
                    'completes_by_deadline': True,
                    'requires_spending_changes': False,
                    'option_id': '0_partial',
                    'method_rank': 1.5
                })

        # Option C: installments
        if 'installments' in considered_methods and max_inst_months > 0:
            options_df = self.dl.get_request_payment_options(req_id)
            inst_options = options_df[options_df['payment_method'] == 'installments']
            for idx, opt in inst_options.iterrows():
                num_pay = int(opt['number_of_payments'])
                if num_pay <= max_inst_months:
                    first_pay_str = str(opt['first_payment_date'])
                    freq_days = int(opt['payment_frequency_days']) if pd.notnull(opt['payment_frequency_days']) else 30
                    pay_amt = float(opt['payment_amount'])
                    
                    p_items = []
                    p_str_list = []
                    cur_p_date = datetime.strptime(first_pay_str, '%Y-%m-%d').date()
                    for k in range(num_pay):
                        p_items.append((cur_p_date, pay_amt))
                        p_str_list.append(f"{cur_p_date.strftime('%Y-%m-%d')}:{self.format_amt(pay_amt)}")
                        cur_p_date = cur_p_date + timedelta(days=freq_days)
                        
                    last_pay_date = p_items[-1][0]
                    min_b, _ = self.simulate_balance_timeline(user_id, req_date_str, payment_plan_items=p_items, spending_changes=None)
                    
                    if min_b >= min_bal_req:
                        candidate_plans.append({
                            'affordability_status': 'affordable_with_plan',
                            'recommended_payment_method': 'installments',
                            'payment_plan': '|'.join(p_str_list),
                            'earliest_date_for_full_payment': earliest_full_date if earliest_full_date else '',
                            'spending_changes_needed': 'none',
                            'total_cost': float(opt['total_payable_amount']),
                            'num_payments': num_pay,
                            'start_date': first_pay_str,
                            'completes_by_deadline': (last_pay_date <= desired_comp_obj),
                            'requires_spending_changes': False,
                            'option_id': str(opt['payment_option_id']),
                            'installment_amount': pay_amt,
                            'method_rank': 3
                        })

        # Option D: wait
        if 'full_payment' in considered_methods and earliest_full_date and datetime.strptime(earliest_full_date, '%Y-%m-%d').date() > req_date_obj and datetime.strptime(earliest_full_date, '%Y-%m-%d').date() <= desired_comp_obj:
            candidate_plans.append({
                'affordability_status': 'affordable_later',
                'recommended_payment_method': 'wait',
                'payment_plan': f"{earliest_full_date}:{self.format_amt(req_amt)}",
                'earliest_date_for_full_payment': earliest_full_date,
                'spending_changes_needed': 'none',
                'total_cost': req_amt,
                'num_payments': 1,
                'start_date': earliest_full_date,
                'completes_by_deadline': True,
                'requires_spending_changes': False,
                'option_id': '0_wait',
                'method_rank': 4
            })

        # Try spending changes proactively - may produce better plans
        sp_changes, sp_str, sp_desc = self.find_spending_changes_needed(user_id, req_date_str, req_amt)
        if sp_changes:
            amt_safe_sp = self.calculate_amount_safe_to_pay(user_id, req_date_str, req_amt, spending_changes=sp_changes)
            earliest_sp = self.calculate_earliest_date_for_full_payment(user_id, req_date_str, req_amt, spending_changes=sp_changes)
            
            # full_payment with spending changes
            if amt_safe_sp >= req_amt and 'full_payment' in considered_methods:
                candidate_plans.append({
                    'affordability_status': 'affordable_with_plan',
                    'recommended_payment_method': 'full_payment',
                    'payment_plan': f"{req_date_str}:{self.format_amt(req_amt)}",
                    'earliest_date_for_full_payment': earliest_sp if earliest_sp else req_date_str,
                    'spending_changes_needed': sp_str,
                    'spending_desc': sp_desc,
                    'total_cost': req_amt,
                    'num_payments': 1,
                    'start_date': req_date_str,
                    'completes_by_deadline': True,
                    'requires_spending_changes': True,
                    'option_id': '0_full_sp',
                    'method_rank': 1
                })

        if candidate_plans:
            best_plan = self.rank_candidate_plans(candidate_plans)
            best_plan['amount_safe_to_pay'] = amount_safe
            best_plan['decision_explanation'] = self.generate_explanation(profile, best_plan, req_amt)
            return best_plan

        formatted_date = datetime.strptime(desired_comp_str, '%Y-%m-%d').strftime('%d %B %Y').lstrip('0')
        return {
            'amount_safe_to_pay': amount_safe,
            'affordability_status': 'not_affordable',
            'recommended_payment_method': 'not_recommended',
            'payment_plan': 'none',
            'earliest_date_for_full_payment': earliest_full_date if earliest_full_date else '',
            'spending_changes_needed': 'none',
            'decision_explanation': f"Do not make this payment by {formatted_date}. None of the available options keeps the {curr} {self.format_with_commas(min_bal_req)} minimum protected."
        }

    def format_amt(self, val):
        if pd.isnull(val) or val == '':
            return ''
        v = float(val)
        if v.is_integer():
            return f"{int(v)}"
        return f"{v:.2f}"

    def format_with_commas(self, val):
        v = float(val)
        if v.is_integer():
            return f"{int(v):,}"
        return f"{v:,.2f}"

    def rank_candidate_plans(self, candidate_plans):
        def rank_key(p):
            return (
                not p['completes_by_deadline'],
                p['requires_spending_changes'],
                p['total_cost'],
                p['method_rank'],
                p['start_date'],
                p['num_payments'],
                p['option_id']
            )
        candidate_plans.sort(key=rank_key)
        return candidate_plans[0]

    def generate_explanation(self, profile, plan, req_amt):
        curr = profile['home_currency']
        min_b = float(profile['minimum_balance_to_keep'])
        method = plan['recommended_payment_method']
        
        if method == 'full_payment':
            if plan.get('spending_changes_needed') != 'none' and 'spending_desc' in plan:
                return f"Adjust expenses ({plan['spending_desc']}), then pay {curr} {self.format_with_commas(req_amt)} today. This leaves at least {curr} {self.format_with_commas(min_b)} available."
            return f"Pay {curr} {self.format_with_commas(req_amt)} today. This leaves at least {curr} {self.format_with_commas(min_b)} available over the next 90 days."
        elif method == 'installments':
            start_date_formatted = datetime.strptime(plan['start_date'], '%Y-%m-%d').strftime('%d %B %Y').lstrip('0')
            return f"Use {plan['num_payments']} installments of {curr} {self.format_with_commas(plan.get('installment_amount', 0))}, starting {start_date_formatted}. This leaves at least {curr} {self.format_with_commas(min_b)} available."
        elif method == 'partial_payment':
            return f"Pay part today and remaining later. This completes the full request and keeps the {curr} {self.format_with_commas(min_b)} minimum protected."
        elif method == 'wait':
            start_date_formatted = datetime.strptime(plan['start_date'], '%Y-%m-%d').strftime('%d %B %Y').lstrip('0')
            return f"Pay {curr} {self.format_with_commas(req_amt)} in full on {start_date_formatted}. Paying earlier would take the balance below the {curr} {self.format_with_commas(min_b)} minimum."
        else:
            return f"Do not proceed with the {curr} {self.format_with_commas(req_amt)} request."
