# -*- coding: utf-8 -*-
"""Youtube Data API.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1icegqlEPRYOzb51ZwyVx6JrR5ANZDyFF

# 連接Youtube Data API
"""

! pip install google-api-python-client

import argparse
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import pandas as pd
import re

# My API KEY for accessing Youtube Data API
DEVELOPER_KEY = 'AIzaSyB74L2kCDwDgQAiVPf8MehllpZ0z9P_pZA'
youtube = build('youtube', 'v3', developerKey=DEVELOPER_KEY)
print(youtube)

"""# 定義重複使用函式 (要從API取得那些資料)
- 獲取類別:
 - 輸出都是list，list裡的元素是以字典為單位，每個字典包含從Youtube Data Api 擷取下來的資訊
 - 可搭配pd.DataFrame()將輸出轉為DF
- 調整類別:
 - 將表格資料轉換成適合分析的資料型態
"""

import pandas as pd

# Set the Channel Id you want to use
channel_id = ['UCSSjn1X6yMBC3AyJ2azeG7A',]

"""## 獲取

### 獲取頻道資訊
"""

# Get the channels information

'''
input : channel_id
output : channel_information_df
'''
def get_channel_stats_df(channel_id):
    from pandas import DataFrame
    all_data = []

    request = youtube.channels().list(
        part = 'snippet,contentDetails,statistics',
        id = ','.join(channel_id)
    )
    response = request.execute()

    # Get the basic information from the channels and store it as DataFrame
    for item in response['items']:
        data = {
            'ChannelNmae':item["snippet"]['title'],
            'Country':item["snippet"]['country'],
            'Publish_Date':item["snippet"]["publishedAt"],
            "ViewCount":item["statistics"]["viewCount"],
            "SubscriberCount":item["statistics"]["subscriberCount"],
            "VideoCount":item["statistics"]["videoCount"],
            "PlaylistID":item['contentDetails']['relatedPlaylists']['uploads']

        }
    all_data.append(data)
    df = DataFrame(all_data)
    return df

"""### 獲取頻道所有影片 ID"""

# get the id of all videos from the chnnel
'''
input : PlaylistID
output : all videos id in the given channel
'''

def get_chnnel_video_id(PlaylistID):
    video_list =[]
    request = youtube.playlistItems().list(
        part = 'snippet,contentDetails',
        playlistId = PlaylistID,
        maxResults = 50
    )
    next_page = True

  # Extract the Whole video
    while next_page:
        response = request.execute()
        data = response['items']

        # Store video Id
        for video in data:
            video_id = video['contentDetails']['videoId']
            if video_id not in video_list:
                video_list.append(video_id)

    # Use nextPageToken to iterate all data
        if 'nextPageToken' in response.keys():
            request = youtube.playlistItems().list(
                part = 'snippet,contentDetails',
                playlistId = PlaylistID,
                pageToken = response['nextPageToken'],
                maxResults = 50
            )

        else:
            next_page = False

    return video_list

"""### 獲取影片資訊"""

# Get the details of videos
def get_video_details(video_list):
    stats_list=[]

    # Can only get 50 videos at a time.
    for i in range(0, len(video_list), 50):
        request= youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_list[i:i+50]
        )
        data = request.execute()
        for video in data['items']:
            id = video['id']
            title=video['snippet']['title']
            published=video['snippet']['publishedAt']
            description=video['snippet']['description']

            # Some video may not have tags
            if 'tags' in video['snippet'].keys():
                tag_count = len(video['snippet']['tags'])
            else:
                tag_count = 0
            video_length = video['contentDetails']["duration"]
            view_count=video['statistics'].get('viewCount',0)
            like_count=video['statistics'].get('likeCount',0)
            dislike_count=video['statistics'].get('dislikeCount',0)
            comment_count=video['statistics'].get('commentCount',0)
            stats_dict=dict(
                id = id,
                video_length = video_length,
                title=title,
                description=description,
                published=published,
                tag_count=tag_count,
                view_count=view_count,
                like_count=like_count,
                dislike_count=dislike_count,
                comment_count=comment_count)
            stats_list.append(stats_dict)

    return stats_list

"""### 獲取單一影片留言"""

def get_video_comments(video_id):
    comments = []
    results = youtube.commentThreads().list(
        part="snippet,replies",
        videoId = video_id,
        maxResults = 100
        ).execute()

    next_page = True
    while next_page:

        # Extract the comments (include replies)
        # Wee add the if to make sure missling value wont break
        for item in results["items"]:
            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"],

            if 'authorChannelId' in item["snippet"]["topLevelComment"]["snippet"].keys():
                id = item["snippet"]["topLevelComment"]["snippet"]['authorChannelId'].get('value')
            else:
                id = None

            if 'authorDisplayName' in item["snippet"]["topLevelComment"]["snippet"].keys():
                user_nsame = item["snippet"]["topLevelComment"]["snippet"]['authorDisplayName']
            else:
                user_nsame = None
            if 'publishedAt' in item["snippet"]["topLevelComment"]["snippet"].keys():
                published = item["snippet"]["topLevelComment"]["snippet"]['publishedAt']

            else:
                published = None

            comment_dict =dict(
                id = id,
                user_nsame = user_nsame,
                comment = comment,
                published =published
            )
            comments.append(comment_dict)
            # Extract the replies from a comment
            if "replies" in item:
                for reply_item in item["replies"]["comments"]:
                    reply_item["snippet"]["textDisplay"]
                    comment = reply_item["snippet"]["textDisplay"]

                    if 'authorChannelId' in reply_item["snippet"].keys():
                        id = reply_item["snippet"]['authorChannelId']['value']
                    else:
                        id = None
                    if 'authorDisplayName' in reply_item["snippet"].keys():
                        user_nsame = reply_item["snippet"]["authorDisplayName"]
                    else:
                        user_name = None

                    if 'publishedAt' in reply_item["snippet"].keys():
                        published = reply_item["snippet"]["publishedAt"]
                    else:
                        published = None

                comment_dict =dict(
                    id = id,
                    user_nsame = user_nsame,
                    comment = comment,
                    published =published
                )
                comments.append(comment_dict)

        # Check if there are more comments
        if "nextPageToken" in results.keys():
            next_page_token = results["nextPageToken"]
            results = youtube.commentThreads().list(
                part="snippet,replies",
                videoId = video_id,
                maxResults = 100,
                pageToken = next_page_token
            ).execute()
        else:
            next_page = False
    return comments

# Retrieve comments
video_comments = get_video_comments('9JK_kaYSnQ0')

# Print comments

"""### 獲取頻道所有留言"""

def get_channel_comments(channel_id):
    comments = []
    results = youtube.commentThreads().list(
        part="snippet,replies",
        allThreadsRelatedToChannelId = channel_id,
        maxResults = 100
        ).execute()

    next_page = True
    ################################################################################
    while next_page:

        # Extract the comments (include replies)
        # Wee add the if to make sure missling value wont break
        for item in results["items"]:
            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"],

            if 'authorChannelId' in item["snippet"]["topLevelComment"]["snippet"].keys():
                id = item["snippet"]["topLevelComment"]["snippet"]['authorChannelId'].get('value')
            else:
                id = None

            if 'authorDisplayName' in item["snippet"]["topLevelComment"]["snippet"].keys():
                user_nsame = item["snippet"]["topLevelComment"]["snippet"]['authorDisplayName']
            else:
                user_nsame = None
            if 'publishedAt' in item["snippet"]["topLevelComment"]["snippet"].keys():
                published = item["snippet"]["topLevelComment"]["snippet"]['publishedAt']

            else:
                published = None

            comment_dict =dict(
                id = id,
                user_nsame = user_nsame,
                comment = comment,
                published =published
            )
            comments.append(comment_dict)
            # Extract the replies from a comment
            if "replies" in item:
                for reply_item in item["replies"]["comments"]:
                    reply_item["snippet"]["textDisplay"]
                    comment = reply_item["snippet"]["textDisplay"]

                    if 'authorChannelId' in reply_item["snippet"].keys():
                        id = reply_item["snippet"]['authorChannelId']['value']
                    else:
                        id = None
                    if 'authorDisplayName' in reply_item["snippet"].keys():
                        user_nsame = reply_item["snippet"]["authorDisplayName"]
                    else:
                        user_name = None

                    if 'publishedAt' in reply_item["snippet"].keys():
                        published = reply_item["snippet"]["publishedAt"]
                    else:
                        published = None

                comment_dict =dict(
                    id = id,
                    user_nsame = user_nsame,
                    comment = comment,
                    published =published
                )
                comments.append(comment_dict)
    ################################################################################
        # Check if there are more comments
        if "nextPageToken" in results.keys():
            next_page_token = results["nextPageToken"]
            results = youtube.commentThreads().list(
                part="snippet,replies",
                allThreadsRelatedToChannelId = channel_id,
                maxResults = 100,
                pageToken = next_page_token
            ).execute()
        else:
            next_page = False


    # Retrieve comments
    return comments

comments = get_channel_comments(channel_id[0])
## 6 min 25
## 81525 rows

"""## 調整

### 移除非中文字體
"""

def remove_non_chinese(text):
    chinese_pattern = re.compile(r'[^\u4e00-\u9fff]+')
    cleaned_text = chinese_pattern.sub('', text)
    return cleaned_text

"""### 調整欄位資料型態"""

def data_type_convert(df):
    df = df.fillna('None')

    for col in df.columns:
        if 'count' in col.lower() and 'country' not in col.lower():
            df[col] = df[col].astype('int')

        if 'video_length' in col:
            df['video_length'] = pd.to_timedelta(df['video_length'])

        if 'published' in col:
            df['published'] = pd.to_datetime(df['published'])

    return df

df_channel_info = data_type_convert(df_channel_info)

channel_video_comments_df = data_type_convert(channel_video_comments_df)

all_channel_comments = data_type_convert(all_channel_comments)

"""#取得所有資料"""

df = get_channel_stats_df(channel_id)
PlaylistID = df.PlaylistID.values[0]
video_list = get_chnnel_video_id(PlaylistID)
stats_list = get_video_details(video_list)
df_channel_info = pd.DataFrame(stats_list)
all_channel_comments = pd.DataFrame(comments)
channel_video_comments_df = pd.DataFrame(video_comments)

df = get_channel_stats_df(channel_id)
df.to_csv('df_channel_stats.csv', index=False,encoding='utf-8')

df.columns

df = data_type_convert(df)

df.info()

"""# 儲存資料"""

# # Store the dataframes
# csv_filename = ['df_channel_info.csv','all_channel_comments.csv','channel_video_comments_df.csv']
# data = [df_channel_info,all_channel_comments,channel_video_comments_df]
# for df,f in zip(data,csv_filename):
#     df.to_csv(f, index=False,encoding='utf-8-sig')

"""# 資聊基本統計分析
- Most views
- Most comments (話題性)
- Most like ()
"""

df_channel_info = pd.read_csv('df_channel_info.csv',encoding='utf-8')
df_channel_info = data_type_convert(df_channel_info)
# all_channel_comments = pd.read_csv('',encoding='utf-8')

# Read large csv file
chunksize = 1000
all_chunks = []  # List to store individual DataFrames

for chunk in pd.read_csv('/content/all_channel_comments.csv', chunksize=chunksize):
    # Process each chunk here
    # For example, you can filter or manipulate data in each chunk
    processed_chunk = chunk  # Replace this with your actual processing logic
    all_chunks.append(processed_chunk)

# Concatenate all the chunks into a single DataFrame
all_channel_comments = pd.concat(all_chunks, ignore_index=True)

max_views_row = df_channel_info[df_channel_info['view_count'] == df_channel_info['view_count'].max()]
max_comments_row = df_channel_info[df_channel_info['comment_count'] == df_channel_info['comment_count'].max()]
max_like_row = df_channel_info[df_channel_info['like_count'] == df_channel_info['like_count'].max()]

"""# 視覺化
- df(頻道基本資訊)
- df_channel_info(頻道個別影片資訊)
- channel_video_comments_df (單一影片留言資訊)
- all_channel_comments (頻道所有留言資訊)
"""

import seaborn as sns
import matplotlib.pyplot as plt
sns.set(style="darkgrid")

df_channel_info.head(2)

"""## 每部影片留言、觀看數、讚數資料分布"""

plt.figure(figsize=(10, 6))
sns.scatterplot(
    data = df_channel_info,
    x = 'view_count',
    y = 'like_count',
    hue = 'comment_count'
                )
# Set title
plt.title("Scatter Plot of Views vs Likes")

# Set axis labels
plt.xlabel("Views")
plt.ylabel("Likes")

# Show legend
plt.legend(title="Comment Counts")

plt.show()

"""## 每部影片觀看數的時間變化
- 早期影片曝光度還是足夠的
- 頻道話題性似乎不高，新影片很少有爆炸性的成長 (影片不容易成為大眾討論的對象)
- 可考慮用其搭指標來評估，而非單純用觀看數

"""

list(df_channel_info.columns)

temp_df = df_channel_info.sort_values(by = 'published')

plt.figure(figsize=(10, 6))

sns.lineplot(x='published', y='view_count', data=temp_df)
plt.title('Time Series Plot with Views')
plt.xlabel('Date')
plt.ylabel('Views')
plt.xticks(rotation=90)
plt.tight_layout()

plt.show()

"""## 每部影片按讚率的隨時間變化
- $\frac{Likes}{Views}=$ 按讚率
- 內容讓觀看的人滿意 (知識 or 娛樂)
"""

plt.figure(figsize=(10, 6))

sns.lineplot(
    x = temp_df['published'],
    y = temp_df['like_count']/temp_df['view_count'])

plt.title('Time Series Plot with Like Rate ')

plt.xlabel('Date')
plt.ylabel('Like Rates')
plt.xticks(rotation=90)
plt.tight_layout()

plt.show()

"""## 每部影片留言率的隨時間變化
-  $\frac{Comments}{Views}=$ 留言率
- 和粉絲的互動感
"""

plt.figure(figsize=(10, 6))

sns.lineplot(
    x = temp_df['published'],
    y = temp_df['comment_count']/temp_df['view_count'])

plt.title('Time Series Plot witn Comment Rate')
plt.xlabel('Date')
plt.ylabel('Comment Rate')
plt.xticks(rotation=90)
plt.tight_layout()

plt.show()

temp_df['comments_rate'] = temp_df['comment_count']/temp_df['view_count']

# Largest comment rate video
temp_df.loc[temp_df['comments_rate'].nlargest(2).index[0]]

# Second largest comment rate video
temp_df.loc[temp_df['comments_rate'].nlargest(2).index[1]]

"""## 擷取欄位文字文字並輸出成文字檔"""

# Extract the text from all_comments_df
all_channel_comments['comment'] = all_channel_comments['comment'].astype(str)
comments = all_channel_comments.comment.apply(remove_non_chinese)
all_comments = str()
for c in comments:
    all_comments += c

# Store all comments on our computer txt file
with open('all_comments.txt', 'w', encoding='utf-8') as f:
    f.write(all_comments)

# Show the total texts numbers
print(len(all_comments))

# Extract the text from all_comments_df
def get_column_text(df,col_name,file_name):
    df[col_name] = df[col_name].astype(str)
    comments = df[col_name].apply(remove_non_chinese)
    all_comments = str()
    for c in comments:
        all_comments += c

    # Store all comments on our computer txt file
    with open(f'{file_name}.txt', 'w', encoding='utf-8') as f:
        f.write(all_comments)
    print('已輸出',file_name)
    # Show the total texts numbers
    print('總中文字數',len(all_comments))

df = pd.read_csv('/content/df_channel_info.csv')

get_column_text(df,'title','title')

"""## 產生文字雲函式"""

# 產生文字雲
def get_world_cloud(file_path, font_path , number = 2, top_k = None, part_of_speech = 'n' ):
    """
    input = text_file
    output = world_cloud
    parameters
    - font_path : (str)
    - number : (int) how many times you want to read the text file
    - top_k : (int) show the top k most frequent words
    - part_of_speech : ['ns', 'n', 'vn', 'v','nr']
    """

    import os
    from jieba import posseg
    from sklearn.feature_extraction.text import TfidfVectorizer
    import matplotlib.pyplot as plt
    from wordcloud import WordCloud

    # Set the size of each chunk in bytes
    # Adjust the size based on your needs
    chunk_size = 10000
    count = 0 # Record the procedure
    all_noun_text = str()

    # Prevent user enter extremely large number
    if number > (os.path.getsize(file_path)//chunk_size)+1:
       raise print("批次讀取檔案次數需小於等於{}".format((os.path.getsize(file_path)//chunk_size)+1))

    # Open the file in binary mode
    with open(file_path, 'r', encoding='utf-8',) as file:

        while count < number:
            chunk = file.read(chunk_size)
            current_position = file.tell()  # Get the current position in bytes
            count += 1

            # 取出名詞
            words_with_pos = posseg.cut(chunk)
            selected_words = [word.word for word in words_with_pos if word.flag.startswith(part_of_speech)]
            selected_text = ' '.join(selected_words)
            all_noun_text = all_noun_text + ' ' + selected_text

            print(f"Processed chunk {count}. Current position: {current_position} bytes")
            remaining_bytes = os.path.getsize(file_path) - current_position
            print(f"Finished processing. Remaining bytes: {remaining_bytes} bytes")

            if not chunk:
                print('已讀取全部文字檔')
                break  # End of file
    print('已讀取部分文字檔')


    # Use Sklearn TFIDF to caculate the frequencies of each words
    vectorizer = TfidfVectorizer(max_features = top_k)
    tfidf_matrix = vectorizer.fit_transform([all_noun_text])
    tfidf_values = tfidf_matrix.toarray()[0]

    # Record word and frequencies to a dictionary
    word_tfidf_dict = dict(zip(vectorizer.get_feature_names_out(), tfidf_values))


    # Generate the world cloud
    wordcloud = WordCloud(
        width=800,
        height=400,
        font_path = font_path,
        background_color='white').generate_from_frequencies(word_tfidf_dict)

    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='spline16')
    plt.axis('off')
    plt.show()

file_path = '/content/all_comments.txt'

## 需自行下載字形
font_path = '/content/NotoSansTC-VariableFont_wght.ttf'

get_world_cloud(file_path,font_path,number = 10,part_of_speech = 'vn' )