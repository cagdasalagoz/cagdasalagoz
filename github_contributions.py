import requests
import os
import datetime

def fetch_github_prs():
    github_token = os.environ.get('GITHUB_TOKEN')
    
    if not github_token:
        print("GITHUB_TOKEN environment variable is not set")
        return []
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    url = "https://api.github.com/search/issues"
    query = "author:cagdasalagoz is:pr -repo:cagdasalagoz/cagdasalagoz"
    
    params = {
        "q": query,
        "sort": "created",
        "order": "desc",
        "per_page": 100
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error fetching GitHub PRs: {response.status_code}")
        print(response.text)
        return []
    
    prs_data = response.json()
    prs = []
    
    for item in prs_data.get("items", []):
        repo_url = item["repository_url"]
        repo_name = repo_url.split("/")[-2] + "/" + repo_url.split("/")[-1]
        
        created_at = datetime.datetime.strptime(item["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        created_date = created_at.strftime("%Y-%m-%d")
        
        state = item["state"]
        if state == "closed":
            if item.get("pull_request", {}).get("merged_at"):
                state = "merged"
        
        pr = {
            "title": item["title"],
            "url": item["html_url"],
            "repo": repo_name,
            "date": created_date,
            "state": state,
            "platform": "GitHub"
        }
        prs.append(pr)
    
    return prs

def save_github_prs_to_file(prs, file_path="github_prs.md"):
    if not prs:
        print("No GitHub PRs to save")
        return
    
    with open(file_path, "w") as f:
        f.write("## My GitHub Contributions\n\n")
        f.write("| Repository | Pull Request | Date | Status |\n")
        f.write("|------------|--------------|------|--------|\n")
        
        for pr in prs:
            status = "✅ Merged" if pr["state"] == "closed" else "⏳ Open"
            f.write(f"| {pr['repo']} | [{pr['title']}]({pr['url']}) | {pr['date']} | {status} |\n")

if __name__ == "__main__":
    prs = fetch_github_prs()
    save_github_prs_to_file(prs)
    print(f"Saved {len(prs)} GitHub PRs to file")