import re
from collections import Counter
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import BertTokenizer, BertForSequenceClassification
from transformers import pipeline
from collections import defaultdict

class NonLLMAnalysis:

    def __init__(self, reddit_data):
        self.reddit_data = reddit_data

    def analyze_mbtitext(self, text, karma_points=0, comment_points=0):
        traits = {
            'E': ['social', 'outgoing', 'talkative', 'lively', 'active', 'party', 'friends', 'chatty', 'extrovert', 'hangout', 'crowd', 'fun', 'vibe', 'bubbly'],
            'I': ['quiet', 'alone', 'introverted', 'reserved', 'solitary', 'reflective', 'introspective', 'shy', 'lowkey', 'chill', 'private', 'solo', 'withdrawn', 'thoughtful'],
            'S': ['facts', 'details', 'practical', 'realistic', 'hands-on', 'experience', 'real', 'concrete', 'grounded', 'traditional', 'literal', 'specific', 'common sense'],
            'N': ['ideas', 'concepts', 'future', 'abstract', 'intuitive', 'theoretical', 'big-picture', 'vision', 'imagine', 'possibilities', 'dream', 'creative', 'innovative', 'open-minded'],
            'T': ['logic', 'reasoning', 'objective', 'analytical', 'rational', 'decisions', 'facts', 'debate', 'critical', 'truth', 'evidence', 'skeptic', 'cold', 'direct', 'fair'],
            'F': ['feelings', 'compassion', 'emotions', 'subjective', 'personal', 'harmony', 'values', 'caring', 'empathy', 'warm', 'support', 'understand', 'sensitive', 'kind'],
            'J': ['organized', 'structured', 'planning', 'decisive', 'predictable', 'control', 'scheduled', 'rule', 'neat', 'on time', 'planner', 'prepared', 'early', 'responsible'],
            'P': ['flexible', 'adaptable', 'spontaneous', 'open', 'improvised', 'curious', 'chill', 'go with the flow', 'last minute', 'laid back', 'unplanned', 'easygoing', 'open-ended']
        }

        words = re.findall(r'\w+', text.lower())
        word_counts = Counter(words)

        scores = {trait: 0 for trait in traits}
        for trait, keywords in traits.items():
            for keyword in keywords:
                scores[trait] += word_counts.get(keyword, 0)

        karma_factor = karma_points / 1000
        comment_factor = comment_points / 1000

        scores['E'] += karma_factor + comment_factor
        scores['I'] -= karma_factor + comment_factor

        scores['N'] += (karma_factor + comment_factor) * 0.5
        scores['S'] -= (karma_factor + comment_factor) * 0.5

        EI_score = scores['E'] - scores['I']
        SN_score = scores['S'] - scores['N']
        TF_score = scores['T'] - scores['F']
        JP_score = scores['J'] - scores['P']

        EI = 'E' if EI_score >= 0 else 'I'
        SN = 'S' if SN_score >= 0 else 'N'
        TF = 'T' if TF_score >= 0 else 'F'
        JP = 'J' if JP_score >= 0 else 'P'

        mbti = EI + SN + TF + JP

        summary_lines = [
            f"MBTI Personality Type Prediction:",
            f"Predicted Type: **{mbti}**",
            f"Dimension Scores:",
            f" - Extraversion (E) vs Introversion (I): {EI_score:.3f}",
            f" - Sensing (S) vs Intuition (N): {SN_score:.3f}",
            f" - Thinking (T) vs Feeling (F): {TF_score:.3f}",
            f" - Judging (J) vs Perceiving (P): {JP_score:.3f}"
        ]
        summary_string = "\n".join(summary_lines)

        return {
            'mbti': mbti,
            'scores': {
                'E vs I': round(EI_score, 3),
                'S vs N': round(SN_score, 3),
                'T vs F': round(TF_score, 3),
                'J vs P': round(JP_score, 3)
            }
        }, summary_string

    def extract_post_comment_text(self):
        text = ""
        for post in self.reddit_data['posts']:
            text += post['post_info']['body'] + " "
        for comment_group in self.reddit_data['comments']:
            for comment in comment_group['comments']:
                text += comment['body'] + " "
        karma_points = self.reddit_data['user_info']['link_karma']
        comment_points = self.reddit_data['user_info']['comment_karma']
        return text.strip(), karma_points, comment_points

    # def big_five(self, text):
    #     model_name = "yohannes/writer-personality-prediction"
    #     tokenizer = AutoTokenizer.from_pretrained(model_name)
    #     model = AutoModelForSequenceClassification.from_pretrained(model_name)
    #     big_five_traits = ["Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"]

    #     inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    #     with torch.no_grad():
    #         outputs = model(**inputs)
    #         logits = outputs.logits

    #     probs = F.softmax(logits, dim=1)
    #     scores = probs[0].tolist()

    #     result = {trait: round(score, 3) for trait, score in zip(big_five_traits, scores)}
    #     return result
    
    

    def personality_detection(self,text):
        tokenizer = BertTokenizer.from_pretrained("Minej/bert-base-personality")
        model = BertForSequenceClassification.from_pretrained("Minej/bert-base-personality")

        inputs = tokenizer(text, truncation=True, padding=True, return_tensors="pt")
        outputs = model(**inputs)
        predictions = outputs.logits.squeeze().detach().numpy()

        label_names = ['Extroversion', 'Neuroticism', 'Agreeableness', 'Conscientiousness', 'Openness']
        result = {label_names[i]: predictions[i] for i in range(len(label_names))}
        output_lines = ["Big Five Personality Prediction:\n"]
        for trait in label_names:
            output_lines.append(f"{trait}: {result[trait]:.4f}")

        result_string = "\n".join(output_lines)
        return result, result_string
    
    def get_emotions(self, text):
        try:
            results = self.emotion_classifier(text)[0]
            return {item['label']: item['score'] for item in results}
        except Exception as e:
            print(f"Error processing emotions for text: {text[:30]}... \nError: {e}")
            return {}

    def emotion_detections(self):
        reddit_data_2 = self.reddit_data.copy()

        self.emotion_classifier = pipeline(
            "text-classification",
            model="nateraw/bert-base-uncased-emotion",
            top_k=None
        )

        emotion_sums = defaultdict(lambda: defaultdict(float))
        emotion_counts = defaultdict(int)
        top_emotion_counter = defaultdict(list)

        # Process posts
        for post in reddit_data_2['posts']:
            text = post['post_info'].get('body') or post['post_info'].get('title') or ""
            emotions = self.get_emotions(text)
            post['emotions'] = emotions

            subreddit = post['subreddit']
            for emotion, score in emotions.items():
                emotion_sums[subreddit][emotion] += score
            emotion_counts[subreddit] += 1

            if emotions:
                top_emotion = max(emotions.items(), key=lambda x: x[1])[0]
                top_emotion_counter[subreddit].append(top_emotion)

        # Process comments
        for comment_group in reddit_data_2['comments']:
            subreddit = comment_group['subreddit']
            for comment in comment_group['comments']:
                text = comment.get('body') or ""
                emotions = self.get_emotions(text)
                comment['emotions'] = emotions

                for emotion, score in emotions.items():
                    emotion_sums[subreddit][emotion] += score
                emotion_counts[subreddit] += 1

                if emotions:
                    top_emotion = max(emotions.items(), key=lambda x: x[1])[0]
                    top_emotion_counter[subreddit].append(top_emotion)

        subreddit_emotion_summary = {}
        subreddit_master = reddit_data_2.get('subreddits_master', {})

        for subreddit, totals in emotion_sums.items():
            count = emotion_counts[subreddit]
            avg_emotions = {
                emotion: round(total / count, 4)
                for emotion, total in totals.items()
            }
            most_common = Counter(top_emotion_counter[subreddit]).most_common(1)[0][0]
            interactions_count = subreddit_master.get(subreddit, {}).get('interactions_count', 0)

            subreddit_emotion_summary[subreddit] = {
                'average_emotions': avg_emotions,
                'most_common_top_emotion': most_common,
                'interactions_count': interactions_count
            }

        top_subreddits = sorted(
            subreddit_emotion_summary.items(),
            key=lambda x: x[1]['interactions_count'],
            reverse=True
        )

        output = "Top Subreddits by Interactions:\n"
        for i, (subreddit, data) in enumerate(top_subreddits, start=1):
            output += f"{i}. r/{subreddit}\n"
            output += f"   Interactions: {data['interactions_count']}\n"
            output += f"   Most Common Top Emotion: {data['most_common_top_emotion']}\n"
            output += "   Average Emotions:\n"
            for emotion, score in data['average_emotions'].items():
                output += f"     {emotion}: {score:.4f}\n"
            output += "\n" 

        return reddit_data_2, subreddit_emotion_summary, output

    
    def print_analysis_summaries(self,mbti_summary_str, bigfive_summary_str, subreddit_emotion_summary_str):
        separator = "\n" + "✨" * 30 + "\n"
        
        full_report = (
            separator +
            "🧠 MBTI Personality Analysis\n" +
            separator +
            mbti_summary_str + "\n" +
            separator +
            "🌟 Big Five Personality Analysis\n" +
            separator +
            bigfive_summary_str + "\n" +
            separator +
            "📊 Subreddit Emotion Summary\n" +
            separator +
            subreddit_emotion_summary_str + "\n" +
            separator +
            "🎉 Thanks for exploring your personality and emotions with us! Stay curious and keep shining! ✨\n"
            + "💬 Feel free to reach out for more insights anytime! 🚀"
        )
        
        print(full_report)



    def run_analysis(self):
        print("Initializing Analysis")
        text, karma_points, comment_points = self.extract_post_comment_text()
        print("Performing MBTI Analysis")
        mbit_result,mbit_string = self.analyze_mbtitext(text=text, karma_points=karma_points, comment_points=comment_points)
        print(mbit_result)
        print("Performing Big Five Analysis")
        bigfive,bigfive_string = self.personality_detection(text=text)
        print(bigfive)
        print("Performing Emotion Analysis:")
        new_reddit_data, subreddit_emotion_summary , output = self.emotion_detections()
        top_subreddits = dict(
            sorted(
                subreddit_emotion_summary.items(),
                key=lambda item: item[1]['interactions_count'],
                reverse=True
            )[:5]  
        )
        self.print_analysis_summaries(mbti_summary_str=mbit_string,bigfive_summary_str=bigfive_string,subreddit_emotion_summary_str=output)
        return {
            'mbti': mbit_result,
            'big_five': bigfive,
            'reddit_data' : new_reddit_data,
            'subreddit_emotion_summary' : subreddit_emotion_summary
        }
    

    
    






