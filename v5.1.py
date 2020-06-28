
import pandas as pd
import argparse
from pathlib import Path
import pdb
from helium import *
from bs4 import BeautifulSoup
import os
from selenium.webdriver.support.ui import Select
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from datetime import datetime
from selenium.webdriver.chrome.options import Options

def get_args(desc="No Desc"):
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-st', '--start_date',
                        help='Start date for date in format "Month date, year" for example "April_25_2020"', default=None)
    parser.add_argument('-ed', '--end_date',
                        help='End date for date in format "Month date, year" for example "April_25_2020"', default=None)
    parser.add_argument('-id', '--email_id', type=int,
                        help='Select the teacher id', choices=[1, 2, 3, 4, 5, 6, 7], default=1)
    parser.add_argument('-fn', '--file_name',
                        help='file with student names and teacher ids to be collected', default=None)
    args = parser.parse_args()
    return args

args = get_args()


def get_soup(elem):
    return BeautifulSoup(elem.get_attribute('innerHTML'), 'html.parser')


def get_datatable(cols, n_rows):
    return pd.DataFrame(columns=cols, index=range(n_rows))


def get_row(elem, tag):
    e = elem.find_elements_by_tag_name(tag)
    return [h.text for h in e]


def get_link(row):
    return row.find_element_by_tag_name('a').get_attribute('href')


def get_table(link=None, tab=None):
    if tab is not None:
        table = (find_all(S('table'))[tab]).web_element
        head = table.find_element_by_tag_name('thead')
        body = table.find_element_by_tag_name('tbody')
    else:
        head = S('table > thead').web_element
        body = S('table > tbody').web_element

    columns = get_row(head, 'th')

    rows = body.find_elements_by_tag_name('tr')
    n_rows = len(rows)

    df = get_datatable(columns, n_rows)

    links = []
    for i, r in enumerate(rows):
        vals = get_row(r, 'td')
        if link is not None:
            links.append((vals[link], get_link(r)))
        for j, v in enumerate(vals):
            df.iloc[i, j] = v
    if link is not None:
        df['links'] = links

    return df

def recursivetable_old(wait_element, escape_element=None, link=None, tab=None):
    try:
        wait_until(Text(wait_element).exists)
    except:
        pass
    if wait_element=='DUE DATE & TIME' and Button('Load More').exists:
        click(Button('Load More'))
        try:
            wait(browser, 10).until(EC.invisibility_of_element_located((By.CLASS_NAME, '_dxnw6v3')))
        except:
            print('collecting limited assignment details')
    if escape_element is not None:
        if Text(escape_element).exists and link is None and not Text(wait_element).exists:
            print('blank activity')
            return pd.DataFrame(columns=[escape_element])
    n = Button('Next')
    if n.exists() and n.is_enabled():
        table_list = []
        while n.is_enabled():
            wait_until(Text(wait_element).exists)
            try:
                table = get_table(link=link, tab=tab)
            except:
                time.sleep(3)
                table = get_table(link=link, tab=tab)
            table_list.append(table)
#             links_list.extend(links)
            click(n)
            n = Button('Next')
        table_list.append(get_table(tab=tab))
        table = pd.concat(table_list)
    else:
        table = get_table(link=link, tab=tab)
    return table
#     if link is not None: return table, links_list


# In[2]:


def login(username, password, visibility='hidden'):
    if visibility == 'hidden':
        chrome_options = Options()
        user_agent = 'I LIKE CHOCOLATE'
        chrome_options.add_argument(f'user-agent={user_agent}')
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(executable_path=os.path.abspath(
            'chromedriver'), options=chrome_options)
        driver.maximize_window()
        set_driver(driver)
        browser = get_driver()
    else:
        browser = start_chrome()
        browser.maximize_window()

    go_to("https://www.khanacademy.org/login")
    write(username, into='Email or username')
    write(password, into='Password')
    click('Log in')
    return browser

def input_date(args):
    wait_until(Text('Last 7 days').exists, timeout_secs=120)
    click('Last 7 days')
    mos = ['January', 'February', 'March', 'April', 'May', 'June',
           'July', 'August', 'September', 'October', 'November', 'December']
    try:
        wait_until(Text('Custom range').exists, timeout_secs=120)
        click('Custom range')
        st = args.start_date.split('_')
        ed = args.end_date.split('_')
        assert st[0] in mos
        assert ed[0] in mos
        start_date = f'{st[0]} {st[1]}, {st[2]}'
        end_date = f'{ed[0]} {ed[1]}, {ed[2]}'
        empty = ''.join([f'\b' for _ in range(50)])
        write(empty + start_date, into='From')
        # pdb.set_trace()
        write(empty + end_date,
              into=browser.find_elements_by_tag_name('input')[-1])
        click('Confirm')
        return [start_date, end_date]
    except:
        print('collecting data of last 7  days')
        return NULL

def create_folder(username, start_date=None, end_date=None):
    root = Path(username)
    if start_date is None:
        folder = Path(
            f'{username}/{datetime.datetime.today().strftime("%Y-%m-%d")}')
    else:
        folder = Path(f'{username}/{start_date}-{end_date}')
    try:
        os.mkdir(str(root))
    except Exception as e:
        print(e)
        print('folder present already')

    try:
        os.mkdir(str(folder))
        os.mkdir(str(folder/'activity_log'))
        os.mkdir(str(folder/'assignments'))
    except Exception as e:
        print(e)
    return folder

def get_soup(elem):
    return BeautifulSoup(elem.get_attribute('innerHTML'), 'html.parser')

def recursivetable(wait_element, escape_element=None, table_no=0):
    try:
        wait_until(Text(wait_element).exists)
    except Exception as e:
        print(e)
        return None

#     if escape_element is not None:
#         if Text(escape_element).exists and not Text(wait_element).exists:
#             print('blank activity')
#             return None

    n = Button('Next')
    if n.exists() and n.is_enabled():
        table_list = []
        while n.is_enabled():
            wait_until(Text(wait_element).exists)
            try:
                table = pd.read_html(browser.page_source)[table_no]
            except:
                time.sleep(3)
                table = pd.read_html(browser.page_source)[table_no]
            table_list.append(table)

            click(n)
            n = Button('Next')
        table_list.append(pd.read_html(browser.page_source)[table_no])
        table = pd.concat(table_list)
    else:
        table = pd.read_html(browser.page_source)[table_no]
    return table

def get_student_data():
    try:
        buttons1 = browser.find_elements_by_tag_name('Button')
        ls1 = [b for b in buttons1 if get_soup(b).getText() == "Activity Log"]
        ls1[-1].click()
        _ = input_date(args)
        # if Text('No results').exists(): raise ValueError
        st_activity = recursivetable(
            'CORRECT/TOTAL PROBLEMS', 'No results')

        st_activity[['Correct Problems', 'Total Problems']] = st_activity.loc[:, 'Correct/Total Problems'].str.split('/', expand=True)
#         st_activity.to_csv(folder/f'activity_log/{name}.csv', index=None)
    except Exception as e:
        print(e)
        print(f'{st} activity not found')
        st_activity = None

    try:
        wait_until(Button('Assignments').exists)
        b = find_all(Button('Assignments'))
        if len(b) == 1:
            time.sleep(5)
            b = find_all(Button('Assignments'))
        bf = b[1] if b[1].x > b[0].x else b[0]
        click(bf)
        load = Button('Load More')
        if load.exists() and load.is_enabled():
            click(load)
        else:
            pass
        as_activity = recursivetable('DUE DATE & TIME')
    #             as_activity.to_csv(
    #             folder/f'assignments/{name}_assignment.csv', index=None)

    except Exception as e:
        print(e)
        print(f'{st} assignment not found')
        as_activity = None


    return st_activity, as_activity



def goto_student(name):
    b = Text('Activity overview')
    click(b)
    click(Text(name))

def get_email_from_id(id):
    USERNAMEs = [f'r30-2020prejoining0{i}@rahmanimission.org' for i in range(0, 8)]
    USERNAME = USERNAMEs[id]  # For Teacher 4
    PASSWORD = 'abc123***'
    return USERNAME, PASSWORD

USERNAME, PASSWORD = get_email_from_id(args.email_id)

# In[5]:


browser = login(USERNAME, PASSWORD, visibility='hidden')


# In[6]:


class_name = f"R30-2020prejoining-0{args.email_id}: Multiple courses"
print(class_name)
wait_until(Text(class_name).exists, timeout_secs=120)
click(class_name)


# In[7]:


student = recursivetable('USERNAME / EMAIL', table_no=1)


# In[8]:


student['Student'] = student['Student name']
student.drop(['Student name', 'Unnamed: 2', 'Unnamed: 3'], inplace=True, axis=1)

# student.head()


# In[12]:


wait_until(Text('Activity overview').exists, timeout_secs=120)
click('Activity overview')

dates = input_date(args)

folder = create_folder(USERNAME, args.start_date, args.end_date)

student.to_csv(f'{USERNAME}/student_names.csv', index=None)


og_table = recursivetable('TOTAL LEARNING MINUTES')
wait_until(Text('Activity overview').exists, timeout_secs=120)
click('Activity overview')

og_table_1 = recursivetable_old('SKILLS LEVELED UP', link=0)


combined = pd.concat([student.reset_index(drop=True), og_table.reset_index(drop=True)], axis=1)
combined = combined.loc[:,~combined.columns.duplicated()]
incomplete = []
combined['delta'] = 0
combined.to_csv(folder/'Progress_all_students.csv', index=None)

# for name, l in tqdm(og_table['links'])
for st, username, name_l in zip(combined.Student, combined.loc[:, 'Username / Email'], og_table_1['links']):
    name, l = name_l
    print(f'---------------*****--------------{st}--------------------****------------')
    # goto_student(st)
    go_to(l)
    wait_until(Text('Activity Log').exists) and wait_until(
        Text('Assignments').exists)

    st_activity, as_activity = get_student_data()

    if st_activity is not None:
        st_activity.to_csv(folder/f'activity_log/{st}-{username}.csv', index=None)
        combined[combined.Student == st]['delta'] = int(combined[combined.Student == st]['Total learning minutes']) - sum(st_activity['Time (min)'])
    else:
        incomplete.append((st, 'activity'))
    if as_activity is not None:
        as_activity.to_csv(folder/f'assignments/{st}-{username}_assignment.csv', index=None)
    else:
        incomplete.append((st, 'assignment'))
combined.to_csv(folder/'Progress_all_students.csv', index=None)

print(incomplete)

# with open()
# browser.close()
browser.quit()
