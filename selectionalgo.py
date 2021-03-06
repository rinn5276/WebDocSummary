#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# encoding=utf-8
"""
Created on Sun May 13 14:53:50 2018

@author: dororo
"""

import os

import jieba
import jieba.analyse
import jieba.posseg as jbps
import requests
from bs4 import BeautifulSoup
from google import google
from opencc import OpenCC
from readability import Document


class Selected(object):
    def __init__(self, name, webname, link, score, description, soup):
        self.name = name
        self.webname = webname
        self.link = link
        self.score = score
        self.description = description
        self.soup = soup

    def display(self):
        print(self.name)
        print(self.score)


class Tag(object):
    def __init__(self, name, weight):
        self.name = name
        self.weight = float(weight)


class Taglist(object):
    def __init__(self):
        self.list = []

    def append(self, tag):
        if type(tag) is Tag:
            self.list.append(tag)

    def isInName(self, name):
        for i, t in enumerate(self.list):
            if t.name == name:
                return i
        return -1

    def __len__(self):
        return len(self.list)

    def __getitem__(self, index):
        return self.list[index]


def selectalgo(search_name, _PATH):
    jenableparallel = True
    try:
        jieba.enable_parallel(2)
    except:
        jenableparallel = False
        print("This env can't enable jieba parallel")
    link = "https://zh.wikipedia.org/wiki/"+search_name
    site = requests.get(link)
    text = BeautifulSoup(site.content, "html.parser")
    wikiTitle = text.find(id="firstHeading").getText()
    text = text.find(id="mw-content-text").extract()
    decolist = ["hatnote", "infobox", "navbox", "vertical-navbox", "toc",
                "mw-editsection", "reference", "plainlist", "plainlists",
                "references-column-width", "refbegin"]  # decompose key word
    for deco in decolist:
        for s in text.find_all(class_=deco):
            s.decompose()
    for s in text.find_all("sup"):
        text.sup.decompose()
    if(text.find(id="noarticletext")):
        print("noarticletext")
        return "noarticletext", None
    selectpos = ["l", "n", "nr", "v", "vn", "eng"]  # select pos
    tags = jieba.analyse.extract_tags(OpenCC('tw2sp').convert(text.getText()), topK=20,
                                      withWeight=True, allowPOS=(selectpos))
    bantag = ["編輯", "條目"]  # ban wiki tag
    taglist = Taglist()
    # tfidffile = open(_PATH+search_name+"textsegmentation.txt", "w")
    for tag, wei in tags:
        if OpenCC('s2twp').convert(tag) in bantag or OpenCC('s2twp').convert(tag) in search_name:
            # tags.remove((tag, wei))
            continue
        print(tag, wei)
        taglist.append(Tag(tag, wei))
        # tfidffile.write("{} {}\n".format(tag, wei))
    # tfidffile.close()
    header = {
        "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.27 Safari/525.13"}
    search_results = google.search(search_name)
    banword = ["ppt", "slide", "pdf", "news", "tv", "facebook.com", "平台", "平臺",
               "books.com", "course", "課程", "偽基", "youtube.com", "cw.com",
               "www.104.com", "udn.com", "KKTIX", "pcschool.com"]
    # banword = []
    selectsite = []
    opcc = OpenCC('tw2sp')
    for i, res in enumerate(search_results):
        print(res.name, "{}/{}".format(i+1, len(search_results)))
        print(res.link)
        banflag = False
        for bw in banword:
            if bw in res.name or bw in res.link:
                print("<{}>".format(bw))
                banflag = True
                break
        if banflag:
            continue
        try:
            response = requests.get(res.link, headers=header)
        except:
            print("some thing error")
        else:
            if "wikipedia" in res.link and False:
                print("iswiki")
                soup = text
            else:
                doc = Document(response.text)
                newhtml = doc.summary()
                converted = opcc.convert(newhtml)
                soup = BeautifulSoup(converted, "html.parser")

            words = jbps.cut(soup.get_text())
            # record = []
            # record.append(res.name+"\n")
            # record.append(res.link+"\n")
            # record.append(res.description+"\n")
            score = 0
            tagset = set()
            for word, _ in words:
                #                print(word)
                index = taglist.isInName(word)
                if index >= 0 and not index in tagset:
                    # record.append("%s %f\n" % (word, taglist[index].weight))
                    score += taglist[index].weight
                    tagset.add(index)
#            print(res.name, score)
            if score > 0:
                webname = ""
                offset = 7
                if res.link[offset] == '/':
                    offset += 1
                for c in res.link[offset:]:
                    if c != '/':
                        webname += c
                    else:
                        break
                print(webname)
                selectsite.append(Selected(res.name, webname,
                                           res.link, score,
                                           res.description, soup))
                # record.append(str(score))
                # with open(_PATH+"score/{}_{:.2f}.txt".format(webname, score), "w") as file:
                #     file.writelines(record)
    if jenableparallel:
        jieba.enable_parallel()
    return wikiTitle, sorted(selectsite, key=lambda s: s.score, reverse=True)[:5]


if __name__ == "__main__":
    #    search_name = input("輸入搜尋項目名稱:")
    #    if search_name=="exit":
    _PATH = os.path.dirname(os.path.abspath(__file__))+"/"
    search_name = "人工智慧"
    _PATH = _PATH+"temp/{}/".format(search_name)
    if not os.path.isdir(_PATH):
        os.mkdir(_PATH)
    print("開始搜尋："+search_name)
    _sitepath = _PATH+"sites/"
    if not os.path.isdir(_sitepath):
        os.mkdir(_sitepath)
    sitefile = open(_PATH+"sites/"+search_name+".txt", "w", encoding="uft-8")
    title, sitelist = selectalgo(search_name, _PATH)
    if title != "noarticletext":
        for site in sitelist:
            site.display()
            sitefile.write(site.name+"\n")
            sitefile.write(site.link+"\n")
            sitefile.write(str(site.score)+"\n")
            sitefile.write("\n")
        sitefile.close()
