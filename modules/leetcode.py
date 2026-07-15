import requests

def get_leetcode_stats(username):
    if not username:
        return None
    url = "https://leetcode.com/graphql"
    query = """
    query userProblemsSolved($username: String!) {
      matchedUser(username: $username) {
        submitStats {
          acSubmissionNum {
            difficulty
            count
          }
        }
      }
    }
    """
    variables = {"username": username}
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        r = requests.post(url, json={"query": query, "variables": variables}, headers=headers, timeout=5)
        data = r.json()
        if "data" in data and data["data"]["matchedUser"]:
            stats = data["data"]["matchedUser"]["submitStats"]["acSubmissionNum"]
            result = {item["difficulty"]: item["count"] for item in stats}
            return result
        return None
    except Exception:
        return None
