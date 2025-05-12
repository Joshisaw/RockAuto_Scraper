from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import undetected_chromedriver as uc
from fake_useragent import UserAgent
from random import randint
import pandas as pd
import time
import os
import re
import csv

# Setup Chrome driver
ua = UserAgent()
options = uc.ChromeOptions()
options.add_argument(f'user-agent={ua.random}')
options.add_argument("--disable-blink-features=AutomationControlled")
driver = uc.Chrome(options=options, service=Service(ChromeDriverManager().install()))

# File paths
read_path = r"V:\07-ProductData\A. Product_Pictures\Intern Startup\Vehicle_Specification\SKU_List.csv"
write_path = r"V:\07-ProductData\A. Product_Pictures\Intern Startup\Vehicle_Specification\Rock_Auto_Scrap_Result"

# Load SKU list
read_file = pd.read_csv(read_path, dtype={'SKU': str})

# Set up csv files to write to
f = open(rf"{write_path}\Rock_Auto_Scrap_Result.csv", 'w', newline='', encoding='utf-8')
writer = csv.writer(f)
header = ["Bosda#", "Vehicle", "Model", "Year", "Position", "Application"]
writer.writerow(header)

s = open(rf"{write_path}\Rock_Auto_Scrap_Result_Full.csv", 'w', newline='', encoding='utf-8')
writer_full = csv.writer(s)
writer_full.writerow(header)

# Preferred brands
preferred_manufacturers = ["moog", "timken", "skf", "ultra-power"]

#get website
website = "https://www.rockauto.com/en/partsearch/?partnum="

#reads through each line
for SKU in read_file.SKU:
    # Normalize SKU
    SKU_num = SKU.strip() # remove whitespace (if any)
    if SKU_num.upper().startswith(("HA", "BF", "BH")):
        SKU_num = SKU_num[2:]
    if SKU_num.upper().endswith("K"):
        SKU_num = SKU_num[:-1]

    # load website
    driver.get(website + SKU_num)

    # Wait for page listings
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'listings-container'))
        )
    except TimeoutException:
        writer.writerow([SKU, "N/A", "N/A", "N/A", "N/A", "N/A"])
        continue

    #Finds all results in listing container and selects individual one
    all_results = driver.find_elements(By.XPATH, '//*[contains(@class, "listing-border-top-line listing-inner-content")]')
    if not all_results:
        print(f"No results found.")
        writer.writerow([SKU, "N/A", "N/A", "N/A", "N/A", "N/A"])
        continue

    # Choose listing by brand or fallback to first
    chosen_index = 0
    matched_brand = None
    for i, result in enumerate(all_results):
        try:
            manufacturer = result.find_element(By.CLASS_NAME, 'listing-final-manufacturer').text.lower()
            category = (result.find_element(By.CLASS_NAME, 'listing-text-row').text)[10:]
            if any(brand in manufacturer for brand in preferred_manufacturers):
                matched_brand = manufacturer
                chosen_index = i
                print(f"{SKU}: Matched brand '{manufacturer}' at index {i}")
                print(f"Category: {category}")
                break
        except NoSuchElementException:
            continue

    # Click part number to open popup
    try:
        chosen_item = all_results[chosen_index]
        part_link = chosen_item.find_element(By.XPATH, './/*[contains(@id, "vew_partnumber")]')
        part_link.click()
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="buyersguidepopup-outer_b"]/div/div/table'))
        )
        model_car_lst = driver.find_elements(By.XPATH, '//*[@id="buyersguidepopup-outer_b"]/div/div/table/tbody/tr')
    except Exception as e:
        print(f"{SKU}: Error opening part details - {e}")
        writer.writerow([SKU, "N/A", "N/A", "N/A", "N/A", "N/A"])
        continue

    #creates empty arrays of all necessary info
    # ig this is fine - future maybe create results[] array that stores all rows
    # current_row = [SKU, Vehicle, Model, Year, Position, Application]
    # current_row[1] = car_make ...
    # results.append(current_row) after creation of current_row
    make = [0] * len(model_car_lst)
    model = [0] * len(model_car_lst)
    year = [0] * len(model_car_lst)
    endyear = [0] * len(model_car_lst)
    position = [0] * len(model_car_lst)
    extra = [0] * len(model_car_lst)
    counter = 0
    
    #for loop goes through all vehicle variations
    for model_car in model_car_lst:
        #finds all info and places in variable
        car_make = model_car.find_element(By.XPATH, './td[1]').text
        make[counter] = car_make
        car_model = model_car.find_element(By.XPATH, './td[2]').text
        model[counter] = car_model
        car_year = model_car.find_element(By.XPATH, './td[3]').text
        year[counter] = car_year

        #formats years, may not need code
        if "-" in car_year:
            start_year = car_year.split("-")[0]  # Full starting year (e.g., 2019)
            end_year = car_year.split("-")[1]   # Full ending year (e.g., 2020)
            parsed_car_yr = f"{start_year}-{end_year}"
            endyear[counter] = end_year
        else:
            parsed_car_yr = car_year  # Use the full year as it is
            endyear[counter] = car_year

        #stores info and advances counter
        counter = counter + 1
    
    #close dialog box
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'dialog-close'))).click()
    counter = 0

    for engine_iteration in model_car_lst:
        search_string = make[counter] + " " + model[counter] + " " + endyear[counter]
        #searches up search string
        input_element = driver.find_element(By.XPATH, '//input[@id="topsearchinput[input]"]')
        input_element.clear()
        input_element.send_keys(search_string)
        time.sleep(.5)
        #finds total engine suggestions
        click_total = driver.find_elements(By.XPATH, '//*[@id="autosuggestions[topsearchinput]"]/tbody/tr')
        click_iterations = len(click_total)-1
        #if not empty
        for autosuggestions in range(click_iterations):
            #enters to get suggestons
            driver.get("https://www.rockauto.com/en/catalog/")
            input_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//input[@id="topsearchinput[input]"]')))
            input_element.send_keys(search_string)
            
            #finds auto auggestion
            time.sleep(.5)
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="autosuggestions[topsearchinput]"]/tbody/tr')))
            click_total = driver.find_elements(By.XPATH, '//*[@id="autosuggestions[topsearchinput]"]/tbody/tr')            
            try:
                #grabs selection suggestion                
                suggested_text = click_total[autosuggestions + 1].text.strip()
                click_total[autosuggestions+1].click()
            except:
                print("ERROR OUT OF EXCEPTION")

            time.sleep(.5)            
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="breadcrumb_location_banner_inner[catalog]"]')))
            breadcrumb_text = driver.find_element(By.XPATH, '//*[@id="breadcrumb_location_banner_inner[catalog]"]').text
            # Split by ">" and get the last part
            breadcrumb_parts = breadcrumb_text.split(">")
            last_part = breadcrumb_parts[-1].strip()  # Extracts the last section
            #goes and finds the correct category Wheel Bearing & Hub
            car_part = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), 'Brake & Wheel Hub')]")))
            if car_part:
                car_part.click()
                part_type = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{category}')]")))
                if part_type:
                    part_type.click()
                    # Check if engine option is present
                    try:
                        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, f"//span[contains(text(), '{SKU_num}')]")))
                        engine_exist = True
                    except TimeoutException:
                        engine_exist = False

                    #enters SKU into filter input to narrow down result
                    input_element = driver.find_elements(By.CLASS_NAME, 'filter-input')
                    if input_element:
                        input_element = input_element[0]
                        input_element.send_keys(SKU_num)
                        input_element.send_keys(Keys.ENTER)
                        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, f"//span[contains(text(), '{SKU_num}')]")))

                        #goes into table and extracts row
                        product_listings = driver.find_elements(By.XPATH, '//table[contains(@class, "nobmp")]/tbody/tr')
                        product_listings = [i for i in product_listings if i.text]

                        #goes through each row and gets index
                        for index, row in enumerate(product_listings):
                            row_text = row.text.lower()
                            
                            #finds car position and extra details
                            if any(brand in row_text for brand in preferred_manufacturers):
                                manufacturer = row.find_element(By.CLASS_NAME, 'listing-final-manufacturer').text.strip()
                                print(f"Chosen manufacturer for {suggested_text}: {manufacturer}")
                                try:
                                    drive_info = row.find_element(By.XPATH, './/div[@class="listing-text-row"]').text
                                except:
                                    engine_exist = False
                                    break
                                if position[counter] == 0:
                                    #splits info based on ;, and puts position and extra into an array
                                    if ";" not in drive_info:
                                        position[counter] = drive_info
                                        if extra[counter] == 0:
                                            extra[counter] = " "
                                    else:
                                        parts = drive_info.split("; ")
                                        position[counter] = parts[0]
                                        if extra[counter] == 0:
                                            extra[counter] = parts[1]
                                        else:
                                            extra[counter] = parts[1] + " " + extra[counter]
                                break
                        #sees if engine exists
                        #print(engine_exist)
                        if engine_exist != True:
                            #inserts prompt depending if engine exists
                            if extra[counter] == 0 or extra[counter] == " ":
                                extra[counter] = "No " + last_part + " "
                            else:
                                extra[counter] = extra[counter] + ", no " + last_part
                            try:
                                writer_full.writerow([SKU, make[counter], model[counter], year[counter], drive_info, last_part])
                            except:
                                writer_full.writerow([SKU, make[counter], model[counter], year[counter], "N/A", "N/A: " + last_part])
                        else:
                            try:
                                writer_full.writerow([SKU, make[counter], model[counter], year[counter], drive_info, last_part])
                            except:
                                writer_full.writerow([SKU, make[counter], model[counter], year[counter], "N/A", "N/A: " + last_part])
                    else:
                        print("ERROR 3")    
                else:
                    print("ERROR 2")
                    writer_full.writerow([SKU, car_make, car_model, car_year, "N/A", last_part])
            else:
                print("ERROR 1")
                writer_full.writerow([SKU, car_make, car_model, car_year, "N/A", last_part])
        #writes to file and advances counter
        writer.writerow([SKU, make[counter], model[counter], year[counter], position[counter], extra[counter]])
        print(SKU, make[counter], model[counter], year[counter], position[counter], extra[counter])
        counter=counter+1
        
driver.quit()
