from bs4 import BeautifulSoup
import requests
import os
import logging
import argparse

logging.basicConfig(filename="script_info.log", level=logging.INFO)

input_string = 'S000004283'
url_main = 'https://www.sec.gov/cgi-bin/browse-edgar?CIK=' + input_string + '&owner=exclude&action=getcompany&Find=Search'
url_sec_gov = 'https://www.sec.gov/'


def get_html(url):
    """
    Returns html page as string by the given url
    """
    response = requests.get(url)
    text = response.text
    response.close()
    return text


def download_save_file(folder, name, url):
    """
    Stores files into a local folder
    :param folder: name of the folder
    :param name: name of the file
    :param url: name of the file's url
    """
    r = requests.get(url)
    full_file_path = os.path.join(folder, name)
    with open(full_file_path, 'wb') as f:
        f.write(r.content)


def process_filling_document_links(folder, links):
    """
    Iterates over links and downloads corresponding files into the folder
    :param folder: name of the folder
    :param links: list of links for downloading
    :return:
    """
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


def find_fillings_document_links(links_page_soup):
    """
    Finds all filling document link in a corresponding page
    :param links_page_soup: page with table with document links
    :return: filling documents links
    """
    filling_document_links = []

    for all_rows in links_page_soup.find_all('tr'):
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
    """
    Goes to the main url with a table of documents links.
    Documents are divided by pages.
    So this function filters documents by label "N-MFP2" on every page.
    Then follows filtered links and downloads corresponding files into the specified folder.

    :param folder: folder to store files to
    :param url: starting(main) url
    :param limit: Maximum number of files that can be downloaded.
    To defend against programming errors or changes of the site layout.
    :return:
    """
    next_url = url
    links_count = 0
    logging.info("Processing url " + next_url)
    if not os.path.exists(folder):
        os.mkdir(folder)
        logging.info("Directory", folder, " was created")

    while links_count < int(limit):
        filling_detail_page_soup = BeautifulSoup(get_html(next_url), features="html.parser")

        fillings_document_links = find_fillings_document_links(filling_detail_page_soup)
        logging.info("Found links. Page: {0}. Links count: {1}".format(next_url, len(fillings_document_links)))
        links_count += len(fillings_document_links)
        process_filling_document_links(folder, fillings_document_links)

        buttons = filling_detail_page_soup.find_all('input')

        next_40 = list(filter(lambda button: button["value"] == "Next 40", buttons))

        if len(next_40) > 0:
            onclick_url = next_40[0]["onclick"]
            next_relative_url = onclick_url[len("parent.location='/"):-1]
            next_url = url_sec_gov + next_relative_url
            logging.info("Found next page: " + next_url)
        else:
            logging.info("Next page not found")
            return


def main():
    parser = argparse.ArgumentParser(description='Download N-MFP2 files')
    parser.add_argument('-f', '--folder', type=str, help='Name for folder holding downloaded files', default='N-MFP2')
    parser.add_argument('-l', '--limit', type=int, help='Maximum number of files that can be downloaded', default=1000)
    args = parser.parse_args()
    process_starting_url(args.folder, url_main, args.limit)


if __name__ == "__main__":
    main()

# python scrap_gov_edgar.py -f N-MFP2 -l 1000
