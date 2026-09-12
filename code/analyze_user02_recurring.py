import pandas as pd

def main():
    df_ev = pd.read_csv('dataset/financial_events.csv')
    u_ev = df_ev[df_ev['user_id'] == 'user_02']

    print("=== Recurring / Monthly Events for user_02 ===")
    for desc, grp in u_ev.groupby('description'):
        cat = grp['category'].iloc[0]
        direction = grp['direction'].iloc[0]
        flex = grp['flexibility'].iloc[0]
        amounts = grp['amount'].dropna().unique()
        dates = grp['event_date'].tolist()
        print(f"Desc: {desc} | Count: {len(grp)} | Cat: {cat} | Dir: {direction} | Flex: {flex}")
        print(f"   Amounts: {amounts} | Dates: {dates[:4]}")
        print('-'*50)

if __name__ == '__main__':
    main()
