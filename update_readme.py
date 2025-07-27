import kde_contributions
import github_contributions
import datetime
import re

def combine_prs():
    kde_prs = kde_contributions.fetch_kde_prs()
    github_prs = github_contributions.fetch_github_prs()
    
    all_prs = kde_prs + github_prs
    all_prs.sort(key=lambda x: x["date"], reverse=True)
    
    return all_prs

def generate_pr_markdown(prs):
    if not prs:
        return "No contributions found."
    
    markdown = "## My Open Source Contributions\n\n"
    markdown += "| Platform | Repository | Pull Request | Date | Status |\n"
    markdown += "|----------|------------|--------------|------|--------|\n"
    
    for pr in prs:
        status = "✅ Merged" if pr["state"] == "closed" or pr["state"] == "merged" else "⏳ Open"
        markdown += f"| {pr['platform']} | {pr['repo']} | [{pr['title']}]({pr['url']}) | {pr['date']} | {status} |\n"
    
    return markdown

def update_readme(pr_markdown):
    with open("README.md", "r") as file:
        content = file.read()
    
    start_marker = "<!-- CONTRIBUTIONS:START -->"
    end_marker = "<!-- CONTRIBUTIONS:END -->"
    
    pattern = f"{start_marker}.*?{end_marker}"
    replacement = f"{start_marker}\n{pr_markdown}\n{end_marker}"
    updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open("README.md", "w") as file:
        file.write(updated_content)

if __name__ == "__main__":
    all_prs = combine_prs()
    pr_markdown = generate_pr_markdown(all_prs)
    update_readme(pr_markdown)
    print(f"README updated with {len(all_prs)} contributions")