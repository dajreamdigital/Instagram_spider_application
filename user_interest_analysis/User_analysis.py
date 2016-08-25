from user_interest_analysis.Instagram_Spider import *
from nltk.stem import WordNetLemmatizer
from nltk.corpus import words
from nltk.corpus import wordnet as wn
from nltk.corpus import wordnet_ic
from matplotlib import pyplot as plt
import math


def store_tag_data(name, tag_data):
    file_name = 'user_tag_data/' + name + '_tag_data.json'
    file = open(file_name, 'w')
    json.dump(tag_data, file)
    file.close()


def load_tag_data(name):
    file_name = 'user_tag_data/' + name + '_tag_data.json'
    file = open(file_name, 'r')
    tag_data = json.load(file)
    file.close()
    return tag_data


def get_data(my_spider, name):
    file_name = 'user_tag_data/' + name + '_tag_data.json'
    if os.path.isfile(file_name):
        tag_data = load_tag_data(name)
    else:
        tag_data = my_spider.get_tag_from_user(name)
        store_tag_data(name, tag_data)
    return tag_data


def clean_up_string(old_string):
    characters = 'QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm'
    new_string = ''
    for char in old_string:
        if char in characters:
            new_string += char
    return new_string.lower()


def get_user_influence_power(user):
    print('start to analyze the social influence power of this user...')
    data = spider.get_user_data(user)
    follower_number = data['followed_by']['count']
    media_list = spider.get_media_from_user(user)
    likes_number = 0
    current_number = 0
    tags_number = 0
    for media in media_list:
        current_number += 1
        print('analyzing user media: ' + media + '(' + str(current_number) + '/20)')
        media_data = spider.get_media_data(media)
        likes_number += media_data['likes']['count']
        tags_list = spider.get_tag_from_media(media)
        tags_number += len(tags_list)
    if len(media_list) > 0:
        likes_number /= len(media_list)
        tags_number /= len(media_list)
    quality = follower_number * 0.000525 + likes_number * 0.989 - tags_number * 6.32
    if quality < 0:
        quality = 0
    if quality > 10000:
        quality = 10000
    if follower_number > 1000000:
        follower_number = 1000000
    if quality == 0 or follower_number == 0:
        power = 0
    else:
        power = math.log(quality * follower_number, 10)
    return power


def successful_rate(successful_list, fail_list):
    successful_number = 0
    fail_number = 0
    for tag_pair in successful_list:
        successful_number += tag_pair[1]
    for tag_pair in fail_list:
        fail_number += tag_pair[1]
    if successful_number == 0 and fail_number == 0:
        my_rate = 0
    else:
        my_rate = successful_number / (successful_number + fail_number)
    return my_rate


def store_dictionary(dict_name, dict_data):
    file = open(dict_name, 'w')
    json.dump(dict_data, file)
    file.close()


def load_dictionary(dict_name):
    file = open(dict_name, 'r')
    dict_data = json.load(file)
    file.close()
    return dict_data


def display_result(data_dict, confidence, username):
    if confidence < 0.4:
        return
    plt.figure(figsize=(9, 9))
    labels = ['family', 'sport', 'animal', 'art', 'technology', 'life', 'fashion', 'food', 'travel']
    colors = ['green', 'blue', 'cyan', 'purple', 'orange', 'pink', 'seagreen', 'red', 'yellow']
    sizes = list()
    explode_list = list()
    max_label = ''
    current_value = 0
    total_value = 0
    for label in labels:
        sizes.append(data_dict[label])
        total_value += data_dict[label]
        if data_dict[label] > current_value:
            current_value = data_dict[label]
            max_label = label
    for label in labels:
        if label == max_label:
            explode_list.append(0.1)
        else:
            explode_list.append(0)
    final_sizes = list()
    if total_value == 0:
        return
    for size in sizes:
        final_sizes.append(size / total_value)
    explode = tuple(explode_list)
    patches, l_text, p_text = plt.pie(final_sizes, explode=explode, labels=labels, colors=colors,
                                      autopct='%3.1f%%', shadow=False, startangle=90, pctdistance=0.7)
    for t in l_text:
        t.set_size = 12
    for t in p_text:
        t.set_size = 4
    plt.axis('equal')
    user_influence = round(get_user_influence_power(username), 2)
    plt.text(-1.2, 1.2, 'username: ' + username, fontsize=15)
    plt.text(-1.2, 1.1, 'confidence: %.2f%%' % (confidence * 100), fontsize=15)
    plt.text(-1.2, 1, 'social influence: ' + str(user_influence), fontsize=15)
    file_name = 'user_analysis_result/' + username + '_analysis.png'
    plt.savefig(file_name, format='png')
    # plt.show()


def combine_dictionary(official_word_list, dictionary):
    official_word_list1 = list(official_word_list)
    for category in dictionary:
        word_list = dictionary[category]
        for word in word_list:
            official_word_list1.append(word)
    official_word_list2 = set(official_word_list1)
    return official_word_list2


def tag2word(tag_list):
    result_list = list()
    for tag_pair in tag_list:
        tag = clean_up_string(tag_pair[0]).lower()
        tag = clean_up_string(tag)
        pos = len(tag)
        while pos > 1:
            word = wordnet_lemmatizer.lemmatize(tag[0:pos])
            if word in wordlist:
                result_list.append((word, tag_pair[1]))
                tag = tag[pos:]
                pos = len(tag)
            else:
                pos -= 1
    print('done...')
    return result_list


def analyze_words(my_words, dictionary):
    similarity_dictionary = dict()
    local_similarity_dictionary = dict()
    distribution_dictionary = dict()
    total_number = 0
    valid_word_count = 0
    for category in dictionary:
        similarity_dictionary[category] = 0
        local_similarity_dictionary[category] = 0
        distribution_dictionary[category] = list()
    distribution_dictionary['unknown'] = list()
    one_tenth = int(len(my_words) / 10)
    current_number = 0
    progress = 0
    total_words = 0
    for word_pair in my_words:
        find_category = False
        current_number += 1
        if current_number > one_tenth:
            progress += 1
            current_number = 0
            print('finish ' + str(progress) + '0%')
        for category in dictionary:
            if word_pair[0] in dictionary[category]:
                if not find_category:
                    valid_word_count += 1
                similarity_dictionary[category] += 10 * word_pair[1]
                total_number += word_pair[1]
                distribution_dictionary[category].append(word_pair)
                find_category = True
        if find_category:
            continue
        try:
            word = wn.synsets(word_pair[0])[0]
            total_number += word_pair[1]
            valid_word_count += 1
        except:
            continue
        for category in dictionary:
            word_list = dictionary[category]
            total_similarity = 0
            total_categary_words = 0
            for test_word in word_list:
                try:
                    test = wn.synsets(test_word)[0]
                except:
                    continue
                try:
                    total_similarity += word.res_similarity(test, brown_ic)
                    total_categary_words += 1
                except:
                    continue
            if total_categary_words > 0:
                similarity_dictionary[category] += word_pair[1] * total_similarity / total_categary_words
                local_similarity_dictionary[category] = total_similarity / total_categary_words
        final_category = 'others'
        for category in local_similarity_dictionary:
            if local_similarity_dictionary[category] > local_similarity_dictionary[final_category]:
                final_category = category
        if local_similarity_dictionary[final_category] > 2.5:
            if local_similarity_dictionary[final_category] > 4:
                if word_pair[0] not in dictionary[final_category]:
                    dictionary[final_category].append(word_pair[0])
            find_category = True
            distribution_dictionary[final_category].append(word_pair)
        if not find_category:
            distribution_dictionary['unknown'].append(word_pair)
    for category in similarity_dictionary:
        if total_number != 0:
            similarity_dictionary[category] /= total_number
    if len(my_words) == 0:
        recognition_rate = 0
    else:
        recognition_rate = valid_word_count / len(my_words)
    percentage_dictionary = dict()

    for category in distribution_dictionary:
        percentage_dictionary[category] = 0
        for word_pair2 in distribution_dictionary[category]:
            percentage_dictionary[category] += word_pair2[1]
            total_words += word_pair2[1]
    for category in percentage_dictionary:
        if total_words != 0:
            percentage_dictionary[category] /= total_words
    print('done...')
    store_dictionary('Instagram_tag_dictionary.json', dictionary)
    return similarity_dictionary, recognition_rate, distribution_dictionary, percentage_dictionary


wordlist = set(words.words())
wordnet_lemmatizer = WordNetLemmatizer()
brown_ic = wordnet_ic.ic('ic-brown.dat')
semcor_ic = wordnet_ic.ic('ic-semcor.dat')
my_dictionary = load_dictionary('Instagram_tag_dictionary.json')
wordlist = combine_dictionary(wordlist, my_dictionary)
spider = InstagramSpider()

username = input('Please give me the user name to analyze: ')
data = get_data(spider, username)
print('data got...')
print('analyzing tags from user: ' + username)
words_from_tags = tag2word(tag_list=data)
print('analyzing words from tags from user: ' + username)
result, rate, distribute_result, percentage_result = analyze_words(my_words=words_from_tags,
                                                                   dictionary=my_dictionary)
print("successful rate of fitting words into dictionary is：%.2f%%" % (rate * 100))
recognize_rate = 1 - percentage_result['unknown']
print("our machine's current recognize rate is：%.2f%%" % (recognize_rate * 100))
display_result(data_dict=percentage_result, confidence=recognize_rate, username=username)

print('end')
