import os
import json
import logging
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

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

def initialize_driver():
    """Initialize and return a Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Use a realistic user agent
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Initialize Chrome driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scrape_microsoft_products() -> Dict:
    """Scrape Microsoft's product page for the latest information using Selenium"""
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
    driver = initialize_driver()
    
    try:
        for category, url in urls.items():
            try:
                logger.info(f"Scraping {url} for {category}")
                driver.get(url)
                
                # Wait for the page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Let JavaScript execute
                driver.implicitly_wait(5)
                
                # Extract product information
                products[category] = {
                    "url": url,
                    "products": []
                }
                
                if category == "Surface":
                    # Wait for Surface products to load
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".feature-list, .m-product-placement-item"))
                    )
                    
                    # Try multiple selectors for Surface products
                    product_elements = driver.find_elements(By.CSS_SELECTOR, ".feature-list .feature, .m-product-placement-item, .c-card")
                    
                    for elem in product_elements:
                        try:
                            # Try different selectors for product names
                            name_elem = elem.find_elements(By.CSS_SELECTOR, ".c-heading, h3, .c-card-title")
                            name = name_elem[0].text if name_elem else "Unknown Surface Product"
                            
                            # Try different selectors for descriptions
                            desc_elem = elem.find_elements(By.CSS_SELECTOR, ".c-paragraph, p")
                            description = desc_elem[0].text if desc_elem else ""
                            
                            if name and not name.lower().startswith("global"):
                                products[category]["products"].append({
                                    "name": name,
                                    "description": description
                                })
                        except Exception as e:
                            logger.warning(f"Error processing a Surface product: {str(e)}")
                
                elif category == "Microsoft 365":
                    # Microsoft 365 products
                    product_elements = driver.find_elements(By.CSS_SELECTOR, ".c-card, .feature")
                    
                    for elem in product_elements:
                        try:
                            name_elem = elem.find_elements(By.CSS_SELECTOR, "h2, h3, .c-heading")
                            name = name_elem[0].text if name_elem else "Unknown Microsoft 365 Product"
                            
                            desc_elem = elem.find_elements(By.CSS_SELECTOR, "p, .c-paragraph")
                            description = desc_elem[0].text if desc_elem else ""
                            
                            if name and not name.lower().startswith("global") and not "user-agent" in name.lower():
                                products[category]["products"].append({
                                    "name": name,
                                    "description": description
                                })
                        except Exception as e:
                            logger.warning(f"Error processing a Microsoft 365 product: {str(e)}")
                
                elif category == "Xbox":
                    # Xbox products
                    product_elements = driver.find_elements(By.CSS_SELECTOR, ".c-product-placement-item, .gamepass-card, .media-card")
                    
                    for elem in product_elements:
                        try:
                            name_elem = elem.find_elements(By.CSS_SELECTOR, "h2, h3, .c-heading, .card-title")
                            name = name_elem[0].text if name_elem else "Unknown Xbox Product"
                            
                            desc_elem = elem.find_elements(By.CSS_SELECTOR, "p, .c-paragraph, .card-text")
                            description = desc_elem[0].text if desc_elem else ""
                            
                            if name and not name.lower().startswith("global") and name.strip() != "":
                                products[category]["products"].append({
                                    "name": name,
                                    "description": description
                                })
                        except Exception as e:
                            logger.warning(f"Error processing an Xbox product: {str(e)}")
                
                else:
                    # Generic product extraction for Windows and Azure
                    # Find headings that might be product names
                    heading_elements = driver.find_elements(By.CSS_SELECTOR, "h2, h3, .c-heading")
                    
                    for elem in heading_elements[:8]:  # Limit to first 8
                        try:
                            name = elem.text.strip()
                            if name and not name.lower().startswith("global") and name != "":
                                # Try to find a description paragraph near the heading
                                try:
                                    # Try to get the parent and then find a paragraph in it
                                    parent = elem.find_element(By.XPATH, "./..")
                                    desc_elems = parent.find_elements(By.CSS_SELECTOR, "p, .c-paragraph")
                                    description = desc_elems[0].text if desc_elems else ""
                                except:
                                    description = ""
                                    
                                products[category]["products"].append({
                                    "name": name,
                                    "description": description
                                })
                        except Exception as e:
                            logger.warning(f"Error processing a {category} heading: {str(e)}")
                
                # Remove duplicates and filter out non-products
                filtered_products = []
                seen_names = set()
                for product in products[category]["products"]:
                    name = product["name"]
                    if (name and 
                        name not in seen_names and 
                        not name.lower().startswith("global") and
                        not "user-agent" in name.lower() and
                        name.strip() != ""):
                        filtered_products.append(product)
                        seen_names.add(name)
                
                products[category]["products"] = filtered_products[:8]  # Limit to 8 products per category
                
                logger.info(f"Scraped {len(products[category]['products'])} products for {category}")
                
            except Exception as e:
                logger.error(f"Error scraping {url} for {category}: {str(e)}")
    
    finally:
        # Always close the driver
        driver.quit()
        
    result = {
        "company": company,
        "categories": products,
        "summary": f"Information about Microsoft's latest products across {len(products)} categories"
    }
    
    # Save to cache
    save_to_cache(company, result)
    
    return result

def scrape_samsung_products() -> Dict:
    """Scrape Samsung's product page for the latest information using Selenium"""
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
    driver = initialize_driver()
    
    try:
        for category, url in urls.items():
            try:
                logger.info(f"Scraping {url} for {category}")
                driver.get(url)
                
                # Wait for the page to load
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Let JavaScript execute
                driver.implicitly_wait(5)
                
                # Extract product information
                products[category] = {
                    "url": url,
                    "products": []
                }
                
                if category == "Mobile":
                    # Wait for mobile products to load
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".product-card, .product-item"))
                    )
                    
                    product_elements = driver.find_elements(By.CSS_SELECTOR, ".product-card, .product-item")
                    
                    for elem in product_elements:
                        try:
                            name_elem = elem.find_elements(By.CSS_SELECTOR, ".product-card__name, .product-item__name, h3")
                            name = name_elem[0].text if name_elem else "Unknown Mobile Product"
                            
                            desc_elem = elem.find_elements(By.CSS_SELECTOR, ".product-card__sub-headline, .product-item__description, p")
                            description = desc_elem[0].text if desc_elem else ""
                            
                            products[category]["products"].append({
                                "name": name,
                                "description": description
                            })
                        except Exception as e:
                            logger.warning(f"Error processing a Mobile product: {str(e)}")
                
                else:
                    # Generic product extraction for other categories
                    product_elements = driver.find_elements(By.CSS_SELECTOR, 
                        ".product-tile, .product-card, .product-item")
                    
                    for elem in product_elements:
                        try:
                            name_elem = elem.find_elements(By.CSS_SELECTOR, 
                                ".product-tile__name, .product-name, h3, .product-card__name")
                            name = name_elem[0].text if name_elem else "Unknown Product"
                            
                            desc_elem = elem.find_elements(By.CSS_SELECTOR, 
                                ".product-tile__description, .product-description, p, .product-card__sub-headline")
                            description = desc_elem[0].text if desc_elem else ""
                            
                            products[category]["products"].append({
                                "name": name,
                                "description": description
                            })
                        except Exception as e:
                            logger.warning(f"Error processing a {category} product: {str(e)}")
                
                # Remove duplicates and limit to 8 products per category
                filtered_products = []
                seen_names = set()
                for product in products[category]["products"]:
                    name = product["name"]
                    if name and name not in seen_names:
                        filtered_products.append(product)
                        seen_names.add(name)
                
                products[category]["products"] = filtered_products[:8]
                
                logger.info(f"Scraped {len(products[category]['products'])} products for {category}")
                
            except Exception as e:
                logger.error(f"Error scraping {url} for {category}: {str(e)}")
    
    finally:
        # Always close the driver
        driver.quit()
        
    result = {
        "company": company,
        "categories": products,
        "summary": f"Information about Samsung's latest products across {len(products)} categories"
    }
    
    # Save to cache
    save_to_cache(company, result)
    
    return result

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
    company = company.lower()
    try:
        if company == "microsoft":
            data = scrape_microsoft_products()
        elif company == "samsung":
            data = scrape_samsung_products()
        else:
            logger.error(f"Unsupported company: {company}")
            return {"error": f"Unsupported company: {company}"}
            
        # Check if we have at least some products, otherwise use fallback
        has_products = False
        for category in data["categories"]:
            if data["categories"][category]["products"]:
                has_products = True
                break
                
        if not has_products:
            logger.warning(f"No products found for {company}, using fallback data")
            
            
        return data
    except Exception as e:
        logger.error(f"Error getting product data for {company}: {str(e)}")
        # Use fallback data if scraping fails
        if company in FALLBACK_DATA:
            logger.info(f"Using fallback data for {company}")
            
        return {"error": f"Error getting data for {company}: {str(e)}"}