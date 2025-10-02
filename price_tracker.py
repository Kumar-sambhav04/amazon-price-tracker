"""
Amazon Price Tracker - Daily Smartphone Price Monitoring
Automated via GitHub Actions
"""

import os
import csv
import time
import random
import datetime
from dotenv import load_dotenv
from amazon_paapi import AmazonApi

# Load environment variables
load_dotenv()

# Amazon API credentials
ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY")
SECRET_KEY = os.getenv("AMAZON_SECRET_KEY")
ASSOCIATE_TAG = os.getenv("AMAZON_ASSOCIATE_TAG")

# Products to track
PRODUCTS = [
    {"brand": "Apple", "product": "iPhone 16 Pro Max", "variant": "256GB", "asin": "B0DGJJM5HZ"},
    {"brand": "Samsung", "product": "Galaxy S24 Ultra", "variant": "256GB", "asin": "B0CS5XW6TN"},
    {"brand": "Google", "product": "Pixel 9 Pro", "variant": "256GB", "asin": "B0FKT2WDXK"},
    {"brand": "OnePlus", "product": "OnePlus 13", "variant": "256GB", "asin": "B0DQ8MGRNX"},
    {"brand": "Motorola", "product": "Edge 50 Ultra", "variant": "256GB", "asin": "B0D7XXKKX6"},
]

# Initialize Amazon API
amazon = AmazonApi(ACCESS_KEY, SECRET_KEY, ASSOCIATE_TAG, "IN")

def get_product_data(asin):
    """Fetch product data from Amazon API"""
    try:
        result = amazon.search_items(keywords=asin, item_count=1)
        return result, None
    except Exception as e:
        return None, str(e)

def extract_product_info(item):
    """Extract price and rating information"""
    price = list_price = rating = reviews = 0
    
    # Extract price data
    if hasattr(item, 'offers') and item.offers:
        listings = getattr(item.offers, 'listings', [])
        if listings:
            listing = listings[0]
            if hasattr(listing, 'price') and hasattr(listing.price, 'amount'):
                price = float(listing.price.amount)
            if hasattr(listing, 'saving_basis') and listing.saving_basis:
                if hasattr(listing.saving_basis, 'amount'):
                    list_price = float(listing.saving_basis.amount)
    
    # Extract rating data
    if hasattr(item, 'customer_reviews'):
        if hasattr(item.customer_reviews, 'star_rating'):
            rating = float(item.customer_reviews.star_rating or 0)
        if hasattr(item.customer_reviews, 'count'):
            reviews = int(item.customer_reviews.count or 0)
    
    # Calculate discount
    discount = 0
    if list_price > 0 and price < list_price:
        discount = round(((list_price - price) / list_price) * 100, 2)
    
    return price, list_price, discount, rating, reviews

def save_to_csv(data, filename="smartphone_prices.csv"):
    """Save data to CSV file"""
    file_exists = os.path.exists(filename)
    
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        if not file_exists:
            writer.writeheader()
        writer.writerows(data)

def main():
    """Main function to collect prices"""
    print("🚀 Starting Daily Price Collection")
    print(f"📅 {datetime.date.today().strftime('%Y-%m-%d')}")
    
    collected_data = []
    
    for product in PRODUCTS:
        print(f"🔄 {product['brand']} {product['product']}...")
        
        result, error = get_product_data(product["asin"])
        
        if error:
            print(f"   ❌ Error: {error}")
            product_data = {
                'date': datetime.date.today().strftime('%Y-%m-%d'),
                'brand': product["brand"],
                'product': product["product"],
                'price': 0, 'list_price': 0, 'discount': 0,
                'rating': 0, 'reviews': 0,
                'asin': product["asin"],
                'status': f'error: {error}'
            }
        else:
            # Process successful response
            items = []
            if hasattr(result, 'items'):
                items = result.items
            elif hasattr(result, 'search_result') and hasattr(result.search_result, 'items'):
                items = result.search_result.items
            
            if not items:
                product_data = {
                    'date': datetime.date.today().strftime('%Y-%m-%d'),
                    'brand': product["brand"],
                    'product': product["product"],
                    'price': 0, 'list_price': 0, 'discount': 0,
                    'rating': 0, 'reviews': 0,
                    'asin': product["asin"],
                    'status': 'no items found'
                }
            else:
                item = items[0]
                price, list_price, discount, rating, reviews = extract_product_info(item)
                
                product_data = {
                    'date': datetime.date.today().strftime('%Y-%m-%d'),
                    'brand': product["brand"],
                    'product': product["product"],
                    'price': price, 'list_price': list_price, 'discount': discount,
                    'rating': rating, 'reviews': reviews,
                    'asin': product["asin"],
                    'status': 'success' if price > 0 else 'no price data'
                }
                
                if price > 0:
                    discount_str = f" ({discount}% off)" if discount > 0 else ""
                    print(f"   ✅ ₹{price:,}{discount_str}")
                else:
                    print(f"   ⚠️  No price data")
        
        collected_data.append(product_data)
        time.sleep(random.uniform(3, 5))  # Be nice to API
    
    # Save data
    save_to_csv(collected_data)
    print(f"💾 Data saved to smartphone_prices.csv")
    
    # Show summary
    successful = len([d for d in collected_data if d['status'] == 'success'])
    print(f"📊 Summary: {successful}/{len(PRODUCTS)} successful")

if __name__ == "__main__":
    main()
