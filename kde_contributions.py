import os
import gitlab
from datetime import datetime, timedelta

# Configuration
GITLAB_URL = "https://invent.kde.org"
GITLAB_PRIVATE_TOKEN = os.getenv("KDE_GITLAB_TOKEN")
YOUR_KDE_GITLAB_USERNAME = "cagdasalagoz"
OUTPUT_FILE = "KDE_CONTRIBUTIONS.md"

# Initialize GitLab API client
gl = gitlab.Gitlab(GITLAB_URL, private_token=GITLAB_PRIVATE_TOKEN)

def get_user_id_and_object(username):
    """Fetches the user ID and the User object from GitLab username."""
    users = gl.users.list(username=username)
    if users:
        return users[0].id, users[0]
    return None, None

def fetch_kde_activity(user_obj, num_days=90):
    """Fetches recent general activity (pushes, issues, comments) for a user object."""
    today = datetime.now()
    cutoff_date = today - timedelta(days=num_days)

    events = user_obj.events.list(
        after=cutoff_date.isoformat(),
        sort="desc",
        per_page=100,
        all=True
    )
    return events

def fetch_kde_merge_requests(user_id, num_days=90):
    """
    Fetches merge requests authored by the user and includes necessary project details.
    Returns a list of dictionaries, each containing 'mr_obj', 'project_name',
    'project_web_url', and 'path_with_namespace'.
    """
    today = datetime.now()
    cutoff_date = today - timedelta(days=num_days)

    partial_mrs = gl.mergerequests.list(
        author_id=user_id,
        created_after=cutoff_date.isoformat(),
        state='all',
        scope='all',
        sort='desc',
        order_by='updated_at',
        per_page=100,
        all=True
    )

    processed_mrs = []
    print(f"Fetching full details for {len(partial_mrs)} merge requests...")
    for mr_partial in partial_mrs: # Rename to mr_partial to avoid confusion
        try:
            # Get the full project object using its ID
            # lazy=False to ensure all project attributes are loaded
            project = gl.projects.get(mr_partial.project_id, lazy=False)
            
            # Get the full merge request object using the project's manager
            full_mr_obj = project.mergerequests.get(mr_partial.iid)
            
            processed_mrs.append({
                'mr_obj': full_mr_obj,
                'project_name': project.name,
                'project_web_url': project.web_url,
                'path_with_namespace': project.path_with_namespace
            })
            time.sleep(0.1) # 100ms delay per MR
        except gitlab.exceptions.GitlabError as e:
            print(f"Error fetching full MR details for ID {mr_partial.id} (IID {mr_partial.iid}) in project {mr_partial.project_id}: {e}")
            continue
    return processed_mrs

def format_activity_for_readme(events, merge_requests_data):
    """Formats GitLab events and merge requests into Markdown for the README."""
    markdown = "### Recent KDE Plasma Contributions (via [invent.kde.org](https://invent.kde.org))\n\n"
    markdown += f"*(Automatically updated on {datetime.now().strftime('%Y-%m-%d %H:%M %Z')})*\n\n"

    combined_activity = []

    # Add general events
    for event in events:
        created_at = datetime.fromisoformat(event.created_at.replace('Z', '+00:00'))
        if event.action_name == 'pushed' and hasattr(event, 'project_name') and hasattr(event, 'project_web_url'):
            combined_activity.append({
                'date': created_at,
                'type': 'Push',
                'description': f"Pushed code to <a href=\"{event.project_web_url}\">{event.project_name}</a>"
            })
        elif event.action_name == 'merged' and hasattr(event, 'target_title') and hasattr(event, 'target_url') and hasattr(event, 'project_name'):
            combined_activity.append({
                'date': created_at,
                'type': 'Merged Event',
                'description': f"Merged MR \"<a href=\"{event.target_url}\">{event.target_title}</a>\" in {event.project_name}"
            })
        elif event.action_name == 'created' and event.target_type == 'issue' and hasattr(event, 'target_title') and hasattr(event, 'target_url') and hasattr(event, 'project_name'):
             combined_activity.append({
                'date': created_at,
                'type': 'Issue',
                'description': f"Created issue \"<a href=\"{event.target_url}\">{event.target_title}</a>\" in {event.project_name}"
            })
        elif event.action_name == 'commented' and hasattr(event, 'note') and hasattr(event.note, 'noteable_type') and hasattr(event, 'project_name'):
            noteable_type = event.note.noteable_type
            note_url = event.note.url
            project_name = event.project_name
            note_content = event.note.body[:70] + '...' if len(event.note.body) > 70 else event.note.body
            markdown_link = f"<a href=\"{note_url}\">commented on a {noteable_type.replace('_',' ')}</a>"
            combined_activity.append({
                'date': created_at,
                'type': 'Comment',
                'description': f"{markdown_link} in {project_name}: \"{note_content}\""
            })

    # Add merge requests
    # Iterate through the dictionaries returned by fetch_kde_merge_requests
    for mr_data in merge_requests_data:
        mr = mr_data['mr_obj'] # The actual MergeRequest object
        project_name = mr_data['project_name']
        project_web_url = mr_data['project_web_url']
        path_with_namespace = mr_data['path_with_namespace']

        mr_state = mr.state.capitalize()
        mr_date = datetime.fromisoformat(mr.updated_at.replace('Z', '+00:00'))

        combined_activity.append({
            'date': mr_date,
            'type': f'Merge Request ({mr_state})',
            # Use the explicitly passed project_web_url and path_with_namespace
            'description': f"MR \"<a href=\"{mr.web_url}\">{mr.title}</a>\" in <a href=\"{project_web_url}\">{path_with_namespace}</a>"
        })

    # Sort combined activity by date, descending
    combined_activity.sort(key=lambda x: x['date'], reverse=True)

    if not combined_activity:
        markdown += "No recent public contributions found.\n\n"
        return markdown

    markdown += "<ul>\n"
    for item in combined_activity:
        formatted_date = item['date'].strftime("%Y-%m-%d %H:%M")
        markdown += f"<li>**{formatted_date}**: {item['type']} - {item['description']}</li>\n"

    markdown += "</ul>\n\n"
    return markdown

if __name__ == "__main__":
    user_id, user_obj = get_user_id_and_object(YOUR_KDE_GITLAB_USERNAME)
    if not user_id or not user_obj:
        print(f"Error: Could not find GitLab user '{YOUR_KDE_GITLAB_USERNAME}' or get user object.")
        exit(1)

    print(f"Fetching activity for user ID: {user_id}")

    recent_events = fetch_kde_activity(user_obj, num_days=180)
    recent_mrs_data = fetch_kde_merge_requests(user_id, num_days=180)

    markdown_content = format_activity_for_readme(recent_events, recent_mrs_data)

    with open(OUTPUT_FILE, "w") as f:
        f.write(markdown_content)

    print(f"Generated {OUTPUT_FILE} with KDE contributions.")
