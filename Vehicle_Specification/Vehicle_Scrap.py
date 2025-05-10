from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from random import randint
import pandas as pd
import time
import os
import re
import csv

C_path = "C:/Users/Joshua.Wang/Desktop/Vehicle_Specification/chromedriver.exe"  # Absolute path
if os.path.exists(C_path):
    print("Chromedriver found!")
else:
    print("Chromedriver not found at:", C_path)

path = os.getcwd()
print(path)
C_options = Options()

# This stores the path of the directory containing the executing script
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# Splits the path into a list of directory names using backslash as the delimiter
dir_lst = ROOT_DIR.split('\\')
# Here we essentially find the parent of the directory containing the executing script
# This is because we want to cd (change directory) to the parent of the directory containing the executing script to access the chromedriver
dir_path = ''
for k in range(len(dir_lst))[:-1]:
    dir_path += (dir_lst[k] + '\\')

os.chdir(dir_path)

# Configure the browser driver
C_options = Options()
C_options.add_argument("--disable-extensions")
C_options.add_argument("--disable-gpu")
C_options.add_argument("--headless")

#Sets up service and driver
service = Service(executable_path=C_path)
driver = webdriver.Chrome(service=service)

#sets up file to read from
path_1 = dir_path + 'Vehicle_Specification'
os.chdir(path_1)
read_file = pd.read_csv('SKU_List.csv', dtype={'SKU':str})

# Set up csv file to write to, this contains necessary info
write_path = path_1 + '\\Rock_Auto_Scrap_Result'
os.chdir(write_path)
write_file = 'Rock_Auto_Scrap_Result.csv'
f = open(write_file, 'w', newline='')
writer = csv.writer(f)
header = ["Bosda#", "Vehicle", "Model", "Year", "Position", "Application"]
writer.writerow(header)

# Set up csv file to write to, this contains all info
write_path_full = path_1 + '\\Rock_Auto_Scrap_Result'
os.chdir(write_path_full)
write_file_full = 'Rock_Auto_Scrap_Result_Full.csv'
s = open(write_file_full, 'w', newline='')
writer_full = csv.writer(s)
header = ["Bosda#", "Vehicle", "Model", "Year", "Position", "Application"]
writer_full.writerow(header)

#get website
website = "https://www.rockauto.com/en/partsearch/?partnum="

#reads through each line
for SKU in read_file.SKU:
    #Removes any K or extra letters from SKU
    SKU_num = SKU
    if re.fullmatch(r"[^a-zA-Z]*[kK]", SKU):
        SKU_num = SKU[:-1]
    full_URL = website + SKU_num
    driver.get(full_URL)

    print("SKU: " + SKU)

    time.sleep(randint(1,3))    

    #Searches all info in listings containers
    result_lst = driver.find_elements(By.CLASS_NAME, 'listings-container')
    #If no result, write NA
    if len(result_lst) == 0:
        writer.writerow([SKU, "N/A", "N/A", "N/A", "N/A", "N/A"])
        continue
    
    #Finds all results in listing container and selects individual one
    all_results = driver.find_elements(By.XPATH, '//*[contains(@class, "listing-border-top-line listing-inner-content")]')
    #Shows priority
    moog_index = -1
    timken_index = -1
    chosen_index = -1

    #Goes through all results given
    for i in range(len(all_results)):
        #Search through all results, finding manufacturer and category
        manufacturer = all_results[i].find_element(By.CLASS_NAME, 'listing-final-manufacturer').text.lower()
        category = all_results[i].find_element(By.CLASS_NAME, 'listing-text-row').text.lower()
        #Sets to index based on results, bu priority
        if manufacturer == "moog" and ("wheel bearing & hub" in category or "wheel bearing" in category or "wheel hub" in category):
            moog_index = i
        elif manufacturer == "timken" and ("wheel bearing & hub" in category or "wheel bearing" in category or "wheel hub" in category):
            timken_index = i
        elif "wheel bearing & hub" in category or "wheel bearing" in category or "wheel hub" in category:
            chosen_index = i

    #if index isn't 0, it sets the actual index
    if moog_index != -1:
        chosen_index = moog_index
    elif timken_index != -1:
        chosen_index = timken_index

    #If index is -1, means doesn't exist
    if chosen_index == -1:
        print("Results are not part of the wheel bearing & hub category")
        writer.writerow([SKU, "N/A", "N/A", "N/A", "N/A", "N/A"])
        continue
    
    #Finds part number on index row
    chosen_item = all_results[chosen_index]
    chosen_item.find_element(By.XPATH, './/*[contains(@id, "vew_partnumber")]').click()
    time.sleep(randint(1,3))    

    #goes through and opens pop up tabel of vehicle specifications
    condition = driver.find_elements(By.XPATH, '//*[@id="buyersguidepopup-outer_b"]/div/div/table')
    if len(condition) != 0:
        model_car_lst = driver.find_elements(By.XPATH, '//*[@id="buyersguidepopup-outer_b"]/div/div/table/tbody/tr')
        print(len(model_car_lst))
    else:
        print(SKU)
        print("Part number couldn't be found in RockAuto")
        f.write(SKU + "," + "N/A, N/A, N/A, N/A, N/A\n")
        continue

    #creates empty arrays of all necessary info
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
        time.sleep(randint(1,3))
    
    #close dialog box
    driver.find_element(By.CLASS_NAME, 'dialog-close').click()
    counter = 0

    for engine_iteration in model_car_lst:
        search_string = make[counter] + " " + model[counter] + " " + endyear[counter]
        #searches up search string
        input_element = driver.find_element(By.XPATH, '//input[@id="topsearchinput[input]"]')
        input_element.clear()
        input_element.send_keys(search_string)
        time.sleep(randint(1,2))
        #finds total engine suggestions
        click_total = driver.find_elements(By.XPATH, '//*[@id="autosuggestions[topsearchinput]"]/tbody/tr')
        #print(click_total[2].text)
        click_iterations = len(click_total)-1
        #if not empty
        for autosuggestions in range(click_iterations):
            #enters to get suggestons
            driver.get("https://www.rockauto.com/en/catalog/")
            time.sleep(randint(3,6))
            input_element = driver.find_element(By.XPATH, '//input[@id="topsearchinput[input]"]')
            input_element.send_keys(search_string)
            time.sleep(randint(1,3))
            #finds auto auggestion
            click_total = driver.find_elements(By.XPATH, '//*[@id="autosuggestions[topsearchinput]"]/tbody/tr')
            try:
                #grabs selection suggestion
                click_total[autosuggestions+1].click()
            except:
                print("ERROR OUT OF EXCEPTION")
            time.sleep(randint(5,8))
            breadcrumb_text = driver.find_element(By.XPATH, '//*[@id="breadcrumb_location_banner_inner[catalog]"]').text
            # Split by ">" and get the last part
            breadcrumb_parts = breadcrumb_text.split(">")
            last_part = breadcrumb_parts[-1].strip()  # Extracts the last section
            #goes and finds the correct category Wheel Bearing & Hub
            input_element = driver.find_elements(By.LINK_TEXT, 'Brake & Wheel Hub')
            if len(input_element) == 1:
                input_element[0].click()
                time.sleep(3)
                input_element = driver.find_elements(By.LINK_TEXT, "Wheel Bearing & Hub")
                if len(input_element) == 1:
                    input_element[0].click()
                    time.sleep(randint(4,7))
                    #enters SKU into filter input to narrow down result
                    input_element = driver.find_elements(By.CLASS_NAME, 'filter-input')
                    if input_element != []:
                        input_element = input_element[0]
                        input_element.send_keys(SKU_num)
                        input_element.send_keys(Keys.ENTER)
                        time.sleep(randint(2, 4))
                        #goes into table and extracts row
                        product_listings = driver.find_elements(By.XPATH, '//table[contains(@class, "nobmp")]/tbody/tr')
                        product_listings = [i for i in product_listings if i.text]
                        engine_exist = False
                        #goes through each row and gets index
                        for index, row in enumerate(product_listings):
                            row_text = row.text.upper()
                            #if part exists after search
                            if index>4:
                                engine_exist = True
                            #finds car position and extra details
                            if "MOOG" in row_text.upper():
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
                        print(engine_exist)
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
                        time.sleep(randint(1,3))
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
        
driver.quit();