from bs4 import BeautifulSoup
import requests
import os
from sys import argv

script_name, folder, limit = argv

input_string = 'S000004283'
url_main = 'https://www.sec.gov/cgi-bin/browse-edgar?CIK=' + input_string + '&owner=exclude&action=getcompany&Find=Search'
url_sec_gov = 'https://www.sec.gov/'


def get_html(url):
    response = requests.get(url)
    text = response.text
    response.close()
    return text


def download_save_file(folder, name, url):
    r = requests.get(url)
    full_file_path = os.path.join(folder, name)
    f = open(full_file_path, 'wb')
    f.write(r.content)
    f.close()


def process_filling_document_links(folder, links):
    for link in links:
        link_soup = BeautifulSoup(get_html(link), features="html.parser")
        name_of_file = link_soup.find("div", {"id": "secNum"}).get_text().split("SEC Accession No.")[1]

        for allRows in link_soup.find_all('tr'):
            tds_in_row = allRows.find_all('td')
            if len(tds_in_row) >= 3:
                maybe_filling = tds_in_row[2]
                if "primary_doc.xml" in maybe_filling.get_text():
                    links_list = maybe_filling.contents
                    file_url = url_sec_gov + links_list[0].get('href')
                    name_of_file = name_of_file.strip() + '.xml'
                    download_save_file(folder, name_of_file, file_url)


def find_fillings_document_links(filling_detail_page_soup):
    filling_document_links = []

    for all_rows in filling_detail_page_soup.find_all('tr'):
        tds_in_row = all_rows.find_all('td')
        if len(tds_in_row) >= 2:
            maybe_filling = tds_in_row[0]
            if "N-MFP2" in maybe_filling.get_text():
                maybe_format = tds_in_row[1]
                links_list = maybe_format.contents
                if len(links_list) > 0:
                    full_link = url_sec_gov + links_list[0].get('href')
                    filling_document_links.append(full_link)

    return filling_document_links


def process_starting_url(folder, url, limit):
    next_url = url
    links_count = 0
    print("Processing url " + next_url)
    if not os.path.exists(folder):
        os.mkdir(folder)
        print("Directory", folder, " was created")

    while True and links_count < int(limit):
        filling_detail_page_soup = BeautifulSoup(get_html(next_url), features="html.parser")

        fillings_document_links = find_fillings_document_links(filling_detail_page_soup)
        print("Found links. Page: " + next_url + ". Links count: " + str(len(fillings_document_links)))
        links_count = links_count + len(fillings_document_links)
        process_filling_document_links(folder, fillings_document_links)

        buttons = filling_detail_page_soup.find_all('input')

        def is_next_40(button):
            return button["value"] == "Next 40"

        next_40 = list(filter(is_next_40, buttons))

        if len(next_40) > 0:
            onclick_url = next_40[0]["onclick"]
            next_relative_url = onclick_url[len("parent.location='/"):-1]
            next_url = url_sec_gov + next_relative_url
            print("Found next page: " + next_url)
        else:
            print("Next page not found")
            return


process_starting_url(folder, url_main, limit)

# python scrap_gov_edgar.py N-MFP2 1000