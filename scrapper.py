import requests
from bs4 import BeautifulSoup
import json


def get_html_content(url):
    """
    Get the HTML content from the specified URL.

    :param url: The URL to fetch the HTML content from.
    :type url: str

    :return: The HTML content of the specified URL, or None if an error occurs.
    :rtype: str
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching HTML content: {e}")
        return None


def extract_news_rows(html_content):
    """
    Function to extract news rows from HTML content.

    Parameters:
    - html_content: The HTML content to extract news rows from (str).

    Returns:
    - List of news rows extracted from the HTML content.
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        news_table = soup.find_all("table")[2]
        return news_table.find_all("tr")
    except IndexError:
        print("Error: Couldn't find news table.")
        return []


def parse_news_row(row):
    """
    Function to parse a news row and extract the rank, title, and link.

    Parameters:
    row (BeautifulSoup.Tag): The row to be parsed.

    Returns:
    dict or None: A dictionary containing the rank, title, and link if successful, or None if an error occurs.
    """
    try:
        if "athing" in row["class"]:
            columns = row.find_all("td")
            rank = int(columns[0].text[:-1])
            news_title = columns[2].find("a")
            title = news_title.text
            link = news_title["href"]
            if link.startswith("item?id="):
                link = f"https://news.ycombinator.com/{link}"
            return {"rank": rank, "title": title, "link": link}
    except Exception as e:
        # print(f"Error parsing news row: {e}")
        return None


def get_comment_links(url):
    """
    Retrieves comment links from the specified URL and returns them as a dictionary.

    Args:
        url (str): The URL from which to retrieve the comment links.

    Returns:
        dict: A dictionary containing the retrieved comment links, with the rank as the key and the link as the value.
    """
    try:
        response = requests.get(url).text
        soup = BeautifulSoup(response, "html.parser")
        comment_link_lines = soup.find_all("span", class_="subline")
        comment_links = {}
        for rank, line in enumerate(comment_link_lines, start=1):
            try:
                comment_link = line.find_all("a")[2]["href"]
                comment_links[rank] = f"https://news.ycombinator.com/{comment_link}"
            except IndexError:
                continue
        return comment_links
    except requests.exceptions.RequestException as e:
        print(f"Error fetching comment links: {e}")
        return {}


def get_comments(url):
    """
    Retrieves comments from the specified URL and returns them as a list.

    Parameters:
    url (str): The URL to fetch comments from.

    Returns:
    list: A list of comments retrieved from the URL. Returns an empty list if an error occurs.
    """
    try:
        response = requests.get(url).text
        soup = BeautifulSoup(response, "html.parser")
        comment_table = soup.find("table", class_="comment-tree")
        comment_list = comment_table.find_all("span", class_="commtext c00")
        comments = [comment.text for comment in comment_list]
        return comments
    except Exception as e:
        print(f"Error fetching comments: {e}")
        return []


def rank_news_comments(url):
    """
    Function to rank news comments based on the provided URL.

    :param url: The URL of the news article.
    :return: A dictionary containing the ranked comments.
    """
    comment_links = get_comment_links(url)
    comment_list = {}
    for rank, link in comment_links.items():
        comments = get_comments(link)
        comment_list[rank] = comments
    return comment_list


def get_news(url):
    """
    Retrieves news data from a given URL and returns a dictionary containing the news rank, title, and link.

    Parameters:
    url (str): The URL to retrieve news data from.

    Returns:
    dict: A dictionary containing the news rank as the key and a dictionary with the title and link as the value. If an error occurs, an empty dictionary is returned.
    """
    try:
        news_data = {}
        for row in extract_news_rows(get_html_content(url)):
            parsed_news = parse_news_row(row)
            if parsed_news:
                news_data[parsed_news["rank"]] = {
                    "title": parsed_news["title"],
                    "link": parsed_news["link"],
                }
        return news_data
    except Exception as e:
        print(f"Error getting news: {e}")
        return {}


def main():
    """
    A function that fetches news from a specified URL and optionally fetches and ranks comments for each news item. It then writes the results to a JSON file named 'output.json'.
    """
    url = "https://news.ycombinator.com/front"

    print("Do you need comments of each thread? (Y/N) ")
    news_result = get_news(url)

    if input().lower() == "y":
        print("Fetching Comments...")
        print("This may take a while...")
        comment_dict = rank_news_comments(url)
    else:
        comment_dict = None

    if comment_dict != None:
        scrap_dict = {}

        for rank, news in news_result.items():
            scrap_dict[rank] = {
                "title": news["title"],
                "link": news["link"],
                "comments": comment_dict.get(rank, [])
            }

        with open("output.json", "w") as out_file:
            json.dump(scrap_dict, out_file, indent=4)
    else:
        with open("output.json", "w") as out_file:
            json.dump(news_result, out_file, indent=4)

    print("Output.json created.")


if __name__ == "__main__":
    main()
