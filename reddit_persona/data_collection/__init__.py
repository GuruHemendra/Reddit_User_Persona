import praw
import datetime
import json
import os
from collections import defaultdict
from urllib.parse import urlparse


class DataCollection:
    """A class to collect and save Reddit user data as JSON."""

    def __init__(self, reddit_client_id, reddit_client_secret, reddit_user_agent):
        """
        Initializes the Reddit client and prepares to collect data.
        
        Args:
            reddit_client_id (str): Reddit client ID.
            reddit_client_secret (str): Reddit client secret.
            reddit_user_agent (str): Reddit user agent.
        """
        # Initialize Reddit client
        self.reddit = praw.Reddit(
            client_id=reddit_client_id,
            client_secret=reddit_client_secret,
            user_agent=reddit_user_agent
        )


    def extract_username(self, user_url):
        """
        Extracts the username from a Reddit user URL.
        
        Args:
            user_url (str): Reddit user URL.
        
        Returns:
            str: Reddit username.
        
        Raises:
            ValueError: If the URL format is invalid.
        """
        path = urlparse(user_url).path
        parts = path.strip("/").split("/")
        if len(parts) >= 2 and parts[0].lower() == "user":
            return parts[1]
        raise ValueError("Invalid Reddit user URL")

    def iso_date(self, utc_timestamp):
        """
        Converts a UTC timestamp to ISO format.
        
        Args:
            utc_timestamp (int): Reddit timestamp in UTC.
        
        Returns:
            str: ISO formatted date string.
        """
        return datetime.datetime.utcfromtimestamp(utc_timestamp).isoformat()

    def fetch_user_info(self, redditor):
        """
        Fetches basic information about a Reddit user.
        
        Args:
            redditor (praw.models.Redditor): Redditor object.
        
        Returns:
            dict: Dictionary containing user information.
        """
        
        try:
            trophies = redditor.trophies()
            trophy_names = [t.name for t in trophies]
        except Exception:
            trophy_names = []
        
        return {
            "username": str(redditor.name),
            "created_at": self.iso_date(redditor.created_utc),
            "link_karma": redditor.link_karma,
            "comment_karma": redditor.comment_karma,
            "trophies": trophy_names,
            "icon_img": getattr(redditor, "icon_img", None),
            "profile_url": f"https://www.reddit.com/user/{redditor.name}"
        }

    def fetch_subreddit_info(self, subreddit):
        """
        Fetches basic information about a subreddit.
        
        Args:
            subreddit (praw.models.Subreddit): Subreddit object.
        
        Returns:
            dict: Dictionary containing subreddit information.
        """
        
        return {
            "title": subreddit.title,
            "public_description": subreddit.public_description,
            "over_18": subreddit.over18,
            "url": f"https://www.reddit.com/r/{subreddit.display_name}"
        }

    def trim_post_info(self, submission):
        """
        Extracts relevant information from a Reddit post.
        
        Args:
            submission (praw.models.Submission): Reddit submission object.
        
        Returns:
            dict: Dictionary containing post details.
        """
        return {
            "title": submission.title,
            "body": submission.selftext,
            "created_at": self.iso_date(submission.created_utc),
            "reddit_url": f"https://www.reddit.com{submission.permalink}",
            "flair": submission.link_flair_text
        }

    def generate_summary(self, user_info, posts, comments, subreddit_interactions):
        """
        Generates a summary of the user's activity.
        
        Args:
            user_info (dict): User's basic info.
            posts (list): List of user posts.
            comments (list): List of user comments.
            subreddit_interactions (dict): Dictionary of subreddit interactions.
        
        Returns:
            dict: Summary information about the user's activity.
        """
        account_created = datetime.datetime.fromisoformat(user_info["created_at"])
        account_age_days = (datetime.datetime.utcnow() - account_created).days
        most_active_sub = max(subreddit_interactions.items(), key=lambda x: x[1], default=(None, 0))[0]
        
        return {
            "total_posts": len(posts),
            "total_comments": sum(len(c["comments"]) for c in comments),
            "unique_subreddits": len(subreddit_interactions),
            "most_active_subreddit": most_active_sub,
            "account_age_days": account_age_days
        }

    def save_json(self, output, user_info):
        """
        Saves the generated output to a JSON file in the 'utils' folder.
        
        Args:
            output (dict): The collected data to save.
            user_info (dict): User information used to name the file.
        """
        # Create the 'utils' folder if it doesn't exist
        utils_folder = os.path.join(os.getcwd(), 'utils')
        os.makedirs(utils_folder, exist_ok=True)
        
        # Define the filename for the output
        filename = os.path.join(utils_folder, f"{user_info['username']}_reddit_export.json")

        # Write the output to the file
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4)
        
        print(f"✅ JSON saved to {filename}")
        return filename

    def generate_reddit_user_json(self, user_url):
        """
        Main method to collect and save Reddit user data as a JSON file.
        
        Args:
            user_url (str): Reddit user profile URL.
        """
        print("Initializing User Data Retrival..")
        username = self.extract_username(user_url)
        redditor = self.reddit.redditor(username)

        user_info = self.fetch_user_info(redditor)
        subreddits_master = {}
        subreddit_interactions_count = defaultdict(int)
        comments_by_post = defaultdict(list)

        # Collect user comments grouped by submission (original post)
        
        for comment in redditor.comments.new(limit=None):
            submission = comment.submission
            sub_name = submission.subreddit.display_name.lower()
            subreddit_interactions_count[sub_name] += 1
            comments_by_post[submission.id].append(comment)

            # Cache subreddit info
            if sub_name not in subreddits_master:
                try:
                    sub = self.reddit.subreddit(sub_name)
                    subreddits_master[sub_name] = self.fetch_subreddit_info(sub)
                except Exception:
                    subreddits_master[sub_name] = {
                        "title": sub_name,
                        "public_description": "",
                        "over_18": None,
                        "url": f"https://www.reddit.com/r/{sub_name}"
                    }

        # Format grouped comments
        print("User comments retrival in process..")
        comments = []
        for submission_id, comments_list in comments_by_post.items():
            submission = comments_list[0].submission
            sub_name = submission.subreddit.display_name.lower()
            post_info = self.trim_post_info(submission)

            user_comments = sorted([
                {
                    "body": comment.body,
                    "created_at": self.iso_date(comment.created_utc),
                    "url": f"https://www.reddit.com{comment.permalink}"
                }
                for comment in comments_list
            ], key=lambda x: x["created_at"])

            comments.append({
                "post_info": post_info,
                "subreddit": sub_name,
                "comments": user_comments
            })

        # Collect user's own posts
        print("User Posts Retrieval in Process..")
        posts = []
        for submission in redditor.submissions.new(limit=None):
            sub_name = submission.subreddit.display_name.lower()
            subreddit_interactions_count[sub_name] += 1

            # Cache subreddit info
            if sub_name not in subreddits_master:
                try:
                    sub = self.reddit.subreddit(sub_name)
                    subreddits_master[sub_name] = self.fetch_subreddit_info(sub)
                except Exception:
                    subreddits_master[sub_name] = {
                        "title": sub_name,
                        "public_description": "",
                        "over_18": None,
                        "url": f"https://www.reddit.com/r/{sub_name}"
                    }

            post_info = self.trim_post_info(submission)
            posts.append({
                "post_info": post_info,
                "subreddit": sub_name
            })

        # Add interaction counts to each subreddit
        for sub_name, count in subreddit_interactions_count.items():
            subreddits_master[sub_name]["interactions_count"] = count

        summary = self.generate_summary(user_info, posts, comments, subreddit_interactions_count)

        output = {
            "exported_at": datetime.datetime.utcnow().isoformat(),
            "user_info": user_info,
            "summary": summary,
            "subreddits_master": subreddits_master,
            "comments": comments,
            "posts": posts
        }

        # Save the output to JSON file
        filename = self.save_json(output, user_info)
        return filename
    



