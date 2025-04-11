import requests
from bs4 import BeautifulSoup
import json
import os
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create cache directory if it doesn't exist
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)


def get_cached_data(company: str) -> Optional[Dict]:
    """Retrieve cached data for a company if it exists"""
    cache_file = os.path.join(CACHE_DIR, f"{company.lower()}_products.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Cache file for {company} exists but contains invalid JSON")
    return None


def save_to_cache(company: str, data: Dict) -> None:
    """Save scraped data to cache"""
    cache_file = os.path.join(CACHE_DIR, f"{company.lower()}_products.json")
    with open(cache_file, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Cached data for {company}")


def scrape_microsoft_products() -> Dict:
    """Scrape Microsoft's product page for the latest information"""
    company = "Microsoft"

    # Try to get cached data first
    cached_data = get_cached_data(company)
    if cached_data:
        logger.info(f"Using cached {company} data")
        return cached_data

    # URLs to scrape
    urls = {
        "Surface": "https://www.microsoft.com/en-us/surface",
        "Windows": "https://www.microsoft.com/en-us/windows",
        "Microsoft 365": "https://www.microsoft.com/en-us/microsoft-365",
        "Xbox": "https://www.xbox.com/en-US/",
        "Azure": "https://azure.microsoft.com/en-us/",
    }

    products = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # Scrape each URL
    for category, url in urls.items():
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract product information
                products[category] = {
                    "url": url,
                    "products": []
                }

                # For Surface products
                if category == "Surface":
                    product_elements = soup.select('.m-product-placement-item')
                    for elem in product_elements:
                        name_elem = elem.select_one('.c-heading')
                        name = name_elem.text.strip() if name_elem else "Unknown Surface Product"

                        desc_elem = elem.select_one('.c-paragraph')
                        description = desc_elem.text.strip() if desc_elem else ""

                        products[category]["products"].append({
                            "name": name,
                            "description": description
                        })

                # For other categories, extract headings
                else:
                    headings = soup.select('h2, h3')
                    for heading in headings[:5]:  # Limit to first 5 for each category
                        products[category]["products"].append({
                            "name": heading.text.strip(),
                            "description": ""
                        })

                logger.info(f"Scraped {len(products[category]['products'])} products for {category}")
            else:
                logger.warning(f"Failed to scrape {url}, status code: {response.status_code}")

        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")

    result = {
        "company": company,
        "categories": products,
        "summary": f"Information about Microsoft's latest products across {len(products)} categories"
    }

    # Save to cache
    save_to_cache(company, result)

    return result


def scrape_samsung_products() -> Dict:
    """Scrape Samsung's product page for the latest information"""
    company = "Samsung"

    # Try to get cached data first
    cached_data = get_cached_data(company)
    if cached_data:
        logger.info(f"Using cached {company} data")
        return cached_data

    # URLs to scrape
    urls = {
        "Mobile": "https://www.samsung.com/us/smartphones/",
        "TV": "https://www.samsung.com/us/televisions-home-theater/tvs/",
        "Home Appliances": "https://www.samsung.com/us/home-appliances/",
        "Computing": "https://www.samsung.com/us/computing/",
        "Displays": "https://www.samsung.com/us/business/displays/"
    }

    products = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    # Scrape each URL
    for category, url in urls.items():
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract product information
                products[category] = {
                    "url": url,
                    "products": []
                }

                # For Mobile products
                if category == "Mobile":
                    product_elements = soup.select('.product-card')
                    for elem in product_elements:
                        name_elem = elem.select_one('.product-card__name')
                        name = name_elem.text.strip() if name_elem else "Unknown Mobile Product"

                        desc_elem = elem.select_one('.product-card__sub-headline')
                        description = desc_elem.text.strip() if desc_elem else ""

                        products[category]["products"].append({
                            "name": name,
                            "description": description
                        })

                # For other categories, extract product tiles
                else:
                    product_elements = soup.select('.product-tile')
                    for elem in product_elements[:8]:  # Limit to first 8 for each category
                        name_elem = elem.select_one('.product-tile__name, .product-name')
                        name = name_elem.text.strip() if name_elem else "Unknown Product"

                        products[category]["products"].append({
                            "name": name,
                            "description": ""
                        })

                logger.info(f"Scraped {len(products[category]['products'])} products for {category}")
            else:
                logger.warning(f"Failed to scrape {url}, status code: {response.status_code}")

        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")

    result = {
        "company": company,
        "categories": products,
        "summary": f"Information about Samsung's latest products across {len(products)} categories"
    }

    # Save to cache
    save_to_cache(company, result)

    return result


def get_latest_products(company: str) -> Dict:
    """Get the latest products for a company, either from cache or by scraping"""
    company = company.lower()
    if company == "microsoft":
        return scrape_microsoft_products()
    elif company == "samsung":
        return scrape_samsung_products()
    else:
        logger.error(f"Unsupported company: {company}")
        return {"error": f"Unsupported company: {company}"}


# Fallback data in case scraping fails
FALLBACK_DATA = {
    "microsoft": {
        "company": "Microsoft",
        "categories": {
            "Surface": {
                "products": [
                    {"name": "Surface Pro 9", "description": "The latest 2-in-1 laptop with touch screen"},
                    {"name": "Surface Laptop 5", "description": "Sleek, ultra-thin laptop"},
                    {"name": "Surface Studio 2+", "description": "All-in-one creative studio"}
                ]
            },
            "Windows": {
                "products": [
                    {"name": "Windows 11", "description": "Latest operating system with improved interface"},
                    {"name": "Windows 365", "description": "Cloud PC experience"}
                ]
            },
            "Microsoft 365": {
                "products": [
                    {"name": "Microsoft 365", "description": "Productivity suite including Word, Excel, PowerPoint"},
                    {"name": "Microsoft Teams", "description": "Collaboration platform"},
                    {"name": "Microsoft Copilot", "description": "AI assistant integrated across Microsoft products"}
                ]
            },
            "Azure": {
                "products": [
                    {"name": "Azure AI", "description": "Suite of AI services"},
                    {"name": "Azure Cloud Services", "description": "Cloud computing platform"},
                    {"name": "Azure Quantum", "description": "Quantum computing solutions"}
                ]
            }
        }
    },
    "samsung": {
        "company": "Samsung",
        "categories": {
            "Mobile": {
                "products": [
                    {"name": "Galaxy S24 Ultra", "description": "Flagship smartphone with advanced camera system"},
                    {"name": "Galaxy Z Fold 5", "description": "Foldable smartphone"},
                    {"name": "Galaxy Z Flip 5", "description": "Compact foldable smartphone"}
                ]
            },
            "TV": {
                "products": [
                    {"name": "Neo QLED 8K", "description": "Premium TV with quantum mini LED technology"},
                    {"name": "The Frame", "description": "TV that doubles as art display"},
                    {"name": "OLED S95C", "description": "OLED TV with Quantum Dot technology"}
                ]
            },
            "Computing": {
                "products": [
                    {"name": "Galaxy Book4 Ultra", "description": "Premium laptop with AMOLED display"},
                    {"name": "Odyssey OLED G9", "description": "Ultra-wide curved gaming monitor"},
                    {"name": "Galaxy Tab S9 Ultra", "description": "Premium tablet with large display"}
                ]
            }
        }
    }
}


def get_product_data(company: str) -> Dict:
    """Get product data with fallback if scraping fails"""
    try:
        data = get_latest_products(company)
        if "error" in data:
            logger.warning(f"Using fallback data for {company}")
            return FALLBACK_DATA.get(company.lower(), {"error": "Company not supported"})
        return data
    except Exception as e:
        logger.error(f"Error getting product data for {company}: {str(e)}")
        return FALLBACK_DATA.get(company.lower(), {"error": "Company not supported"})