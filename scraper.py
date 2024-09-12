import requests
from bs4 import BeautifulSoup
import csv
import time
import re


def scrape_category(category_url, category_name):
    products = []
    page = 1
    while True:
        url = f"{category_url}?p={page}"
        print(f"Scraping {category_name} - Page {page}")
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        items = soup.find_all("li", class_="item product product-item")
        if not items:
            print(f"No more items found for {category_name}. Moving to next category.")
            break

        for item in items:
            product = {}
            product_name_elem = item.find("a", class_="product-item-link")
            product["name"] = product_name_elem.text.strip()
            product["category"] = category_name
            product["price"] = item.find("span", class_="price").text.strip()
            product["url"] = product_name_elem["href"]

            # Extract brand from the product description
            # <span class="prod_brand"><a href="https://www.spinneyslebanon.com/default/brands/noix-choco">By Noix &amp; Choco</a></span>
            brand_elem = item.find("span", class_="prod_brand")
            brand_text = brand_elem.text.strip() if brand_elem else "N/A"
            if "By " in brand_text:
                product["brand"] = brand_text.replace("By ", "")
            else:
                product["brand"] = "N/A"

            # Extract size from the product description
            size_elem = item.find("span", class_="prod_weight")
            if size_elem:
                size_text = size_elem.get_text(strip=True)
                product["size"] = size_text
            else:
                product["size"] = "1 piece"

            # Calculate price per unit
            product["price_per_unit"] = calculate_price_per_unit(
                product["price"], product["size"]
            )

            # Get image URL
            img_tag = item.find("img", class_="product-image-photo")
            if img_tag:
                product["image"] = (
                    img_tag.get("data-src") or img_tag.get("src") or "N/A"
                )
            else:
                product["image"] = "N/A"

            products.append(product)

        print(f"Completed scraping page {page} of {category_name}")
        page += 1
        time.sleep(1)
    return products


def format_float(value):
    return f"{value:.5f}".rstrip('0').rstrip('.')

def calculate_price_per_unit(price, size):
    price_value = float(re.search(r"\d+(\.\d+)?", price).group())
    size_match = re.search(r"(\d+(\.\d+)?)\s*(\w+(?:\s+\w+)*)", size, re.IGNORECASE)
    if size_match:
        size_value = float(size_match.group(1))
        size_unit = size_match.group(3).lower()

        # Handle "PER KG" case
        if size_unit == "per kg":
            return f"${format_float(price_value)} per kg"

        # Convert all weights to grams and all volumes to ml
        if size_unit in ["g", "ml", "s", "pcs", "pc", "."]:
            converted_size = size_value
        elif size_unit in ["kg", "l"]:
            converted_size = size_value * 1000
        elif size_unit == "gb":
            return f"${format_float(price_value / size_value)} per GB"
        else:
            return f"${format_float(price_value)} for {size}"

        # Calculate price per unit
        price_per_unit = price_value / converted_size

        # Format output
        if size_unit in ["g", "kg"]:
            return f"${format_float(price_per_unit * 1000)} per kg"
        elif size_unit in ["ml", "l"]:
            if price_per_unit < 0.00001:
                return f"${format_float(price_per_unit * 1000)} per L"
            else:
                return f"${format_float(price_per_unit)} per ml"
        elif size_unit in ["s", "pcs", "pc", "."]:
            return f"${format_float(price_value)} per piece"

    return f"${format_float(price_value)} for {size}"


def save_to_csv(products, filename):
    keys = set()
    for product in products:
        keys.update(product.keys())

    print(f"Saving {len(products)} products to {filename}")
    with open(filename, "w", newline="", encoding="utf-8") as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=sorted(keys))
        dict_writer.writeheader()
        dict_writer.writerows(products)
    print(f"Successfully saved data to {filename}")


def save_all_to_csv(all_products, filename):
    keys = set()
    for product in all_products:
        keys.update(product.keys())

    print(f"Saving {len(all_products)} products to {filename}")
    with open(filename, "w", newline="", encoding="utf-8") as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=sorted(keys))
        dict_writer.writeheader()
        dict_writer.writerows(all_products)
    print(f"Successfully saved all data to {filename}")


def main():
    categories = [
        (
            "Hair Care",
            "https://www.spinneyslebanon.com/default/beauty-personal-care/hair-care.html",
        ),
        (
            "Body Care",
            "https://www.spinneyslebanon.com/default/beauty-personal-care/body-care.html",
        ),
        (
            "Facial Skin Care",
            "https://www.spinneyslebanon.com/default/beauty-personal-care/facial-skin-care.html",
        ),
        (
            "Feminine Care",
            "https://www.spinneyslebanon.com/default/beauty-personal-care/feminine-care.html",
        ),
        # Add more categories here
    ]

    all_products = []

    for category_name, category_url in categories:
        print(f"\nStarting to scrape {category_name}...")
        products = scrape_category(category_url, category_name)
        all_products.extend(products)
        print(f"Completed scraping {category_name}. Total products: {len(products)}")

    # Save all products to a single CSV file
    save_all_to_csv(all_products, "all_products.csv")

    # Optionally, you can still save individual category files
    for category_name, _ in categories:
        category_products = [p for p in all_products if p["category"] == category_name]
        filename = f"{category_name.replace(' ', '_').lower()}.csv"
        save_to_csv(category_products, filename)

    print(f"Total products scraped across all categories: {len(all_products)}")

if __name__ == "__main__":
    print("Starting the web scraper...")
    main()
    print("Web scraping completed. Check the generated CSV files for results.")
