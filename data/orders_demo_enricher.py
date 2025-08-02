import pandas as pd
from datetime import datetime, timedelta, time, UTC
import random

def random_evening_time():
    # 60% evening (17:00-23:00)
    if random.random() < 0.6:
        hour = random.randint(17, 23)
    else:
        hour = random.choice(list(range(5, 24)) + [0, 1])
    minute = random.randint(0, 59)
    return time(hour=hour, minute=minute)

def assign_datetime(base_date):
    t = random_evening_time()
    return datetime.combine(base_date.date(), t, tzinfo=UTC)

CARRIERS = [
    ('UPS', '1Z' + ''.join(['#']*16), 'https://wwwapps.ups.com/WebTracking/track?track=yes&trackNums={tn}'),
    ('FedEx', '6' + ''.join(['#']*11), 'https://www.fedex.com/apps/fedextrack/?tracknumbers={tn}'),
    ('DHL', 'JD' + ''.join(['#']*16), 'https://www.dhl.com/en/express/tracking.html?AWB={tn}'),
    ('USPS', '94' + ''.join(['#']*20), 'https://tools.usps.com/go/TrackConfirmAction?tLabels={tn}')
]

def random_tracking(carrier_tpl):
    carrier, pattern, url_tpl = carrier_tpl
    # Replace '#' with random digit
    tn = ''.join([str(random.randint(0,9)) if c == '#' else c for c in pattern])
    url = url_tpl.format(tn=tn)
    return carrier, tn, url

def generate_orders_demo_enriched():
    # Load orders
    orders = pd.read_csv('orders_demo.csv')

    # Parameters
    start_date = datetime(2016, 1, 1, tzinfo=UTC)
    end_date = datetime(2017, 1, 1, tzinfo=UTC)

    # Prepare output
    output = []

    # Sort for sequential processing
    orders_sorted = orders.sort_values(['user_id', 'order_number'])

    # Process per user
    for user_id, group in orders_sorted.groupby('user_id'):
        group = group.sort_values('order_number')
        created_at_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
        created_at = assign_datetime(created_at_date)

        for idx, row in group.iterrows():
            carrier_tpl = random.choice(CARRIERS)
            carrier, tn, url = random_tracking(carrier_tpl)

            out = row.to_dict()
            out['created_at'] = created_at.isoformat(sep=' ')  # UTC timestamp with +00:00
            out['tracking_number'] = tn
            out['shipping_carrier'] = carrier
            out['tracking_url'] = url
            output.append(out)

            if not pd.isna(row['days_since_prior_order']):
                # Add days, then assign a new plausible time (simulate real reordering)
                created_at_date += timedelta(days=int(row['days_since_prior_order']))
                created_at = assign_datetime(created_at_date)

    orders_with_enrichment = pd.DataFrame(output)
    orders_with_enrichment.to_csv('orders_demo_enriched.csv', index=False)
    print("orders_demo_enriched.csv created.")

if __name__ == "__main__":
    generate_orders_demo_enriched()
