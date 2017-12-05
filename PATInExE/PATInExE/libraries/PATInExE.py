# -*- coding: utf-8 -*-
"""
Created on Sun Dec  3 12:24:25 2017

@author: root
"""

import re
import glob
from nltk import word_tokenize
import pickle
#pickle is used for writing the training_X and training_y data to file as a list. It serializes the list structure
import numpy as np
from sklearn.naive_bayes import MultinomialNB

def getTokenList(inpString):
    split_text = word_tokenize(inpString)
    word_list=[]
    current_string=""
    for word in split_text:
        if word[0].isupper():
            if len(current_string)>0:
                current_string = current_string+" "+word
            else:
                current_string = word
        else:
            if len(current_string)>0:
                word_list.append(current_string)
                current_string = ""
            word_list.append(word)
    return word_list

def getCountVector(file,search_words):
    with open(file, 'r',encoding='cp1252') as myfile:
        sentence=re.sub(r'[\t\n]',' . ',myfile.read())
    token_list = getTokenList(sentence)
    count_vector=[]
    for search_word in search_words:
        count_vector.append(token_list.count(search_word))
    return count_vector

def generateTrainingData():
    #loading the journey related words to search_words
    with open("./PATInExE Data/journey_words.txt", 'r',encoding='cp1252') as myfile:
        search_words=[x.strip() for x in myfile.readlines()]

    #X and y for multinomialNB
    X=[]
    y=[]
    sample_weight=[]

    #building X and y corresponding to potential files
    files = glob.glob("./PATInExE Data/Training_emails/Potential/*.txt")
    for file in files:
        countVector=getCountVector(file,search_words)
        if sum(countVector)<10:
            sample_weight.append(2)
        else:
            sample_weight.append(1)
        X.append(countVector)
        y.append(1)

    #building X and y corresponding to potential files
    files = glob.glob("./PATInExE Data/Training_emails/Non-Potential/*.txt")
    for file in files:
        X.append(getCountVector(file,search_words))
        y.append(0)
        sample_weight.append(3)

    with open('./PATInExE Data/training_X.txt', 'wb') as fp:
        pickle.dump(X, fp)

    with open('./PATInExE Data/training_y.txt', 'wb') as fp:
        pickle.dump(y, fp)

    with open('./PATInExE Data/sample_weight.txt', 'wb') as fp:
        pickle.dump(sample_weight, fp)

def classifyEmailFromFile():

    #X and y for multinomialNB
    with open("./PATInExE Data/training_X.txt", "rb") as fp:
        X=np.array(pickle.load(fp))

    with open("./PATInExE Data/training_y.txt", "rb") as fp:
        y=np.array(pickle.load(fp))

    with open("./PATInExE Data/sample_weight.txt", "rb") as fp:
        sample_weight=np.array(pickle.load(fp))

    #loading the journey related words to search_words
    with open("./PATInExE Data/journey_words.txt", 'r',encoding='cp1252') as myfile:
        search_words=[x.strip() for x in myfile.readlines()]

    #creating the multinobialNB model
    mnnb_model=MultinomialNB(alpha=1.0/3)
    mnnb_model.fit(X,y,sample_weight)

    #reading and evaluating the content of the new_mail.txt in the inbox
    newMail="./PATInExE Data/Inbox/new_mail.txt"
    newMailCountVector = getCountVector(newMail,search_words)

    #predicting the class of new_mail
    prediction = mnnb_model.predict(np.array(newMailCountVector).reshape(1,-1)) #reshape(1,-1) is used to avoid warning of deprecation in Scikit 0.19 and above

    if prediction[0]==0:
        return False
    elif prediction[0]==1:
        return True

def getMaximumIndex(checkList,keyIndex):
    '''This function returns the index of the list (checkList, which is a list of lists with n=2),
    which holds the maximum value at the specified index (keyIndex)'''
    maximumIndex=0
    for index,item in enumerate(checkList):
        if item[keyIndex]>checkList[maximumIndex][keyIndex]:
            maximumIndex=index
    return maximumIndex


def getKeys(item):
    '''used for sorting a list of lists, based on a given element of inner list'''
    return item[0].start()

def isCancelMail(emailContent):
    checkRExpression = re.compile("(has|is) (been)? cancelled (successfully|as|according)")
    if (re.search(checkRExpression,emailContent))!=None:
        return True
    else:
        return False

def getDepartureTime(emailContent,taggedIndices):
    timeValue="N/A" #return value
    timeTagIndices=[]
    #to store only the DEPART-TIME tag matches
    for index,taggedItem in enumerate(taggedIndices):
        if taggedItem[1]=='DEPART-TIME':
            timeTagIndices.append([taggedItem[0],index])

    timeBefore=[]
    timeAfter=[]
    nearestTimePairScore=[]

    #finding the closest TIME tagged matches and its score for each DEPART-TIME tag
    for timeTagIndex in timeTagIndices:

        #finding the TIME tagged match before the DEPART-TIME
        for i in range(timeTagIndex[1],0,-1):
            if taggedIndices[i][1]=='TIME':
                timeBefore=[taggedIndices[i][0],i]
                break

        #finding the TIME tagged match before the DEPART-TIME
        for i in range(timeTagIndex[1],len(taggedIndices)):
            if taggedIndices[i][1]=='TIME':
                timeAfter=[taggedIndices[i][0],i]
                break

        scoreBefore=0
        scoreAfter=0

        #calculating score for TIME match before the DEPART-TIME match
        if len(timeBefore)>0:
            #calculate the distance between the indices
            distanceBefore=timeTagIndex[0].start()-timeBefore[0].start()
            #calculate number of sentences in between, based on number of dots(.)
            sentenceInBetween=emailContent[ timeBefore[0].end() : timeTagIndex[0].start() ].count('.')
            #calculating score
            #maximum score is 1000
            #distance is substracted
            #for each sentence, 100 is substracted beacause if they are in different sentences their chance of being tag-data pair is less
            scoreBefore=1000-distanceBefore-(sentenceInBetween*100)

        #calculating score for TIME match before the DEPART-TIME match
        if len(timeAfter)>0:
            distanceAfter=timeAfter[0].start()-timeTagIndex[0].end()
            sentenceInBetween=emailContent[ timeTagIndex[0].end() : timeAfter[0].start() ].count('.')
            scoreAfter=1000-distanceAfter-(sentenceInBetween*100)

        #find which score is maximum
        if scoreBefore>0 or scoreAfter>0:
            #append the maximum score and corresponding time match object as a pair to a list
            if scoreBefore>scoreAfter:
                nearestTimePairScore.append([scoreBefore,timeBefore[1]])
            else:
                nearestTimePairScore.append([scoreAfter,timeAfter[1]])

    #getting the corresponding TIME value from the taggedIndices
    #maximum value of score from nearestTimePairScore is choosen as the data of interest
    try:
        timeValue = taggedIndices[nearestTimePairScore[getMaximumIndex(nearestTimePairScore,0)][1] ][0].group()
    finally:
        return timeValue.strip()

def getDepartureDate(emailContent,taggedIndices):
    dateValue="N/A" #return value
    dateTagIndices=[]
    #to store only the DEPART-DATE tag matches
    for index,taggedItem in enumerate(taggedIndices):
        if taggedItem[1]=='DEPART-DATE':
            dateTagIndices.append([taggedItem[0],index])

    dateBefore=[]
    dateAfter=[]
    nearestDatePairScore=[]

    #finding the closest DATE tagged matches and its score for each DEPART-DATE tag
    for dateTagIndex in dateTagIndices:

        #finding the DATE tagged match before the DEPART-DATE
        for i in range(dateTagIndex[1],0,-1):
            if taggedIndices[i][1]=='DATE':
                dateBefore=[taggedIndices[i][0],i]
                break

        #finding the DATE tagged match before the DEPART-DATE
        for i in range(dateTagIndex[1],len(taggedIndices)):
            if taggedIndices[i][1]=='DATE':
                dateAfter=[taggedIndices[i][0],i]
                break

        scoreBefore=0
        scoreAfter=0

        #calculating score for DATE match before the DEPART-DATE match
        if len(dateBefore)>0:
            #calculate the distance between the indices
            distanceBefore=dateTagIndex[0].start()-dateBefore[0].start()
            #calculate number of sentences in between, based on number of dots(.)
            sentenceInBetween=emailContent[ dateBefore[0].end() : dateTagIndex[0].start() ].count('.')
            #calculating score
            #maximum score is 1000
            #distance is substracted
            #for each sentence, 100 is substracted beacause if they are in different sentences their chance of being tag-data pair is less
            scoreBefore=1000-distanceBefore-(sentenceInBetween*100)

        #calculating score for DATE match before the DEPART-DATE match
        if len(dateAfter)>0:
            distanceAfter=dateAfter[0].start()-dateTagIndex[0].end()
            sentenceInBetween=emailContent[ dateTagIndex[0].end() : dateAfter[0].start() ].count('.')
            scoreAfter=1000-distanceAfter-(sentenceInBetween*100)

        #find which score is maximum
        if scoreBefore>0 or scoreAfter>0:
            #append the maximum score and corresponding date match object as a pair to a list
            if scoreBefore>scoreAfter:
                nearestDatePairScore.append([scoreBefore,dateBefore[1]])
            else:
                nearestDatePairScore.append([scoreAfter,dateAfter[1]])

    #getting the corresponding DATE value from the taggedIndices
    #maximum value of score from nearestDatePairScore is choosen as the data of interest
    try:
        dateValue = taggedIndices[nearestDatePairScore[getMaximumIndex(nearestDatePairScore,0)][1] ][0].group()
    finally:
        return dateValue.strip()


def getTicketID(emailContent,taggedIndices):
    ticketIdValue="N/A" #return value
    ticketIdTagIndices=[]
    #to store only the TICKET-ID-TAG tag matches
    for index,taggedItem in enumerate(taggedIndices):
        if taggedItem[1]=='TICKET-ID-TAG':
            ticketIdTagIndices.append([taggedItem[0],index])

    ticketIdBefore=[]
    ticketIdAfter=[]
    nearestTicketIdPairScore=[]

    #finding the closest TICKET-ID tagged matches and its score for each TICKET-ID-TAG tag
    for ticketIdTagIndex in ticketIdTagIndices:

        #finding the TICKET-ID tagged match before the TICKET-ID-TAG
        for i in range(ticketIdTagIndex[1],0,-1):
            if taggedIndices[i][1]=='TICKET-ID':
                ticketIdBefore=[taggedIndices[i][0],i]
                break

        #finding the TICKET-ID tagged match before the TICKET-ID-TAG
        for i in range(ticketIdTagIndex[1],len(taggedIndices)):
            if taggedIndices[i][1]=='TICKET-ID':
                ticketIdAfter=[taggedIndices[i][0],i]
                break

        scoreBefore=0
        scoreAfter=0

        #calculating score for TICKET-ID match before the TICKET-ID-TAG match
        if len(ticketIdBefore)>0:
            #calculate the distance between the indices
            distanceBefore=ticketIdTagIndex[0].start()-ticketIdBefore[0].start()
            #calculate number of sentences in between, based on number of dots(.)
            sentenceInBetween=emailContent[ ticketIdBefore[0].end() : ticketIdTagIndex[0].start() ].count('.')
            #calculating score
            #maximum score is 1000
            #distance is substracted
            #for each sentence, 100 is substracted beacause if they are in different sentences their chance of being tag-data pair is less
            scoreBefore=1000-distanceBefore-(sentenceInBetween*100)

        #calculating score for TICKET-ID match before the TICKET-ID-TAG match
        if len(ticketIdAfter)>0:
            distanceAfter=ticketIdAfter[0].start()-ticketIdTagIndex[0].end()
            sentenceInBetween=emailContent[ ticketIdTagIndex[0].end() : ticketIdAfter[0].start() ].count('.')
            scoreAfter=1000-distanceAfter-(sentenceInBetween*100)

        #find which score is maximum
        if scoreBefore>0 or scoreAfter>0:
            #append the maximum score and corresponding ticketId match object as a pair to a list
            if scoreBefore>scoreAfter:
                nearestTicketIdPairScore.append([scoreBefore,ticketIdBefore[1]])
            else:
                nearestTicketIdPairScore.append([scoreAfter,ticketIdAfter[1]])

    #getting the corresponding TICKET-ID value from the taggedIndices
    #maximum value of score from nearestTicketIdPairScore is choosen as the data of interest
    try:
        ticketIdValue = taggedIndices[nearestTicketIdPairScore[getMaximumIndex(nearestTicketIdPairScore,0)][1] ][0].group()
    finally:
        return ticketIdValue.strip()


def getPhoneNumber(emailContent,taggedIndices):
    phonenumberValue="N/A" #return value
    phonenumberTagIndices=[]
    #to store only the PHONE-NO-TAG tag matches
    for index,taggedItem in enumerate(taggedIndices):
        if taggedItem[1]=='PHONE-NO-TAG':
            phonenumberTagIndices.append([taggedItem[0],index])

    phonenumberBefore=[]
    phonenumberAfter=[]
    nearestPhonenoPairScore=[]

    #finding the closest PHONE-NO tagged matches and its score for each PHONE-NO-TAG tag
    for phonenumberTagIndex in phonenumberTagIndices:

        #finding the PHONE-NO tagged match before the PHONE-NO-TAG
        for i in range(phonenumberTagIndex[1],0,-1):
            if taggedIndices[i][1]=='PHONE-NO':
                phonenumberBefore=[taggedIndices[i][0],i]
                break

        #finding the PHONE-NO tagged match before the PHONE-NO-TAG
        for i in range(phonenumberTagIndex[1],len(taggedIndices)):
            if taggedIndices[i][1]=='PHONE-NO':
                phonenumberAfter=[taggedIndices[i][0],i]
                break

        scoreBefore=0
        scoreAfter=0

        #calculating score for PHONE-NO match before the PHONE-NO-TAG match
        if len(phonenumberBefore)>0:
            #calculate the distance between the indices
            distanceBefore=phonenumberTagIndex[0].start()-phonenumberBefore[0].start()
            #calculate number of sentences in between, based on number of dots(.)
            sentenceInBetween=emailContent[ phonenumberBefore[0].end() : phonenumberTagIndex[0].start() ].count('.')
            #calculating score
            #maximum score is 1000
            #distance is substracted
            #for each sentence, 100 is substracted beacause if they are in different sentences their chance of being tag-data pair is less
            scoreBefore=1000-distanceBefore-(sentenceInBetween*100)

        #calculating score for PHONE-NO match before the PHONE-NO-TAG match
        if len(phonenumberAfter)>0:
            distanceAfter=phonenumberAfter[0].start()-phonenumberTagIndex[0].end()
            sentenceInBetween=emailContent[ phonenumberTagIndex[0].end() : phonenumberAfter[0].start() ].count('.')
            scoreAfter=1000-distanceAfter-(sentenceInBetween*100)

        #find which score is maximum
        if scoreBefore>0 or scoreAfter>0:
            #append the maximum score and corresponding phonenumber match object as a pair to a list
            if scoreBefore>scoreAfter:
                nearestPhonenoPairScore.append([scoreBefore,phonenumberBefore[1]])
            else:
                nearestPhonenoPairScore.append([scoreAfter,phonenumberAfter[1]])

    #getting the corresponding PHONE-NO value from the taggedIndices
    #maximum value of score from nearestPhonenoPairScore is choosen as the data of interest
    try:
        phonenumberValue = taggedIndices[nearestPhonenoPairScore[getMaximumIndex(nearestPhonenoPairScore,0)][1] ][0].group()
    finally:
        phonenumberValue = re.sub(r"[^(0-9)]"," ",phonenumberValue)
        return phonenumberValue.strip()

def getJourneySource(emailContent,taggedIndices):
    sourceValue="N/A" #return value
    sourceTagIndices=[]
    #to store only the SOURCE-TAG tag matches
    for index,taggedItem in enumerate(taggedIndices):
        if taggedItem[1]=='SOURCE-TAG':
            sourceTagIndices.append([taggedItem[0],index])

    sourceBefore=[]
    sourceAfter=[]
    nearestSourcePairScore=[]

    #finding the closest PLACE tagged matches and its score for each SOURCE-TAG tag
    for sourceTagIndex in sourceTagIndices:

        #finding the PLACE tagged match before the SOURCE-TAG
        for i in range(sourceTagIndex[1],0,-1):
            if taggedIndices[i][1]=='PLACE':
                sourceBefore=[taggedIndices[i][0],i]
                break

        #finding the PLACE tagged match before the SOURCE-TAG
        for i in range(sourceTagIndex[1],len(taggedIndices)):
            if taggedIndices[i][1]=='PLACE':
                sourceAfter=[taggedIndices[i][0],i]
                break

        scoreBefore=0
        scoreAfter=0

        #calculating score for PLACE match before the SOURCE-TAG match
        if len(sourceBefore)>0:
            #calculate the distance between the indices
            distanceBefore=sourceTagIndex[0].start()-sourceBefore[0].start()
            #calculate number of sentences in between, based on number of dots(.)
            sentenceInBetween=emailContent[ sourceBefore[0].end() : sourceTagIndex[0].start() ].count('.')
            #calculating score
            #maximum score is 1000
            #distance is substracted
            #for each sentence, 100 is substracted beacause if they are in different sentences their chance of being tag-data pair is less
            scoreBefore=1000-distanceBefore-(sentenceInBetween*100)

        #calculating score for PLACE match before the SOURCE-TAG match
        if len(sourceAfter)>0:
            distanceAfter=sourceAfter[0].start()-sourceTagIndex[0].end()
            sentenceInBetween=emailContent[ sourceTagIndex[0].end() : sourceAfter[0].start() ].count('.')
            scoreAfter=1000-distanceAfter-(sentenceInBetween*100)

        #find which score is maximum
        if scoreBefore>0 or scoreAfter>0:
            #append the maximum score and corresponding source match object as a pair to a list
            if scoreBefore>scoreAfter:
                nearestSourcePairScore.append([scoreBefore,sourceBefore[1]])
            else:
                nearestSourcePairScore.append([scoreAfter,sourceAfter[1]])

    #getting the corresponding PLACE value from the taggedIndices
    #maximum value of score from nearestSourcePairScore is choosen as the data of interest
    try:
        dataIndex = nearestSourcePairScore[getMaximumIndex(nearestSourcePairScore,0)][1]
        sourceValue = taggedIndices[ dataIndex ][0].group()
        del taggedIndices[dataIndex]
    finally:
        return sourceValue.strip()

def getJourneyDestination(emailContent,taggedIndices):
    destinationValue="N/A" #return value
    destinationTagIndices=[]
    #to store only the DESTINATION-TAG tag matches
    for index,taggedItem in enumerate(taggedIndices):
        if taggedItem[1]=='DESTINATION-TAG':
            destinationTagIndices.append([taggedItem[0],index])

    destinationBefore=[]
    destinationAfter=[]
    nearestDestinationPairScore=[]

    #finding the closest PLACE tagged matches and its score for each DESTINATION-TAG tag
    for destinationTagIndex in destinationTagIndices:

        #finding the PLACE tagged match before the DESTINATION-TAG
        for i in range(destinationTagIndex[1],0,-1):
            if taggedIndices[i][1]=='PLACE':
                destinationBefore=[taggedIndices[i][0],i]
                break

        #finding the PLACE tagged match before the DESTINATION-TAG
        for i in range(destinationTagIndex[1],len(taggedIndices)):
            if taggedIndices[i][1]=='PLACE':
                destinationAfter=[taggedIndices[i][0],i]
                break

        scoreBefore=0
        scoreAfter=0

        #calculating score for PLACE match before the DESTINATION-TAG match
        if len(destinationBefore)>0:
            #calculate the distance between the indices
            distanceBefore=destinationTagIndex[0].start()-destinationBefore[0].start()
            #calculate number of sentences in between, based on number of dots(.)
            sentenceInBetween=emailContent[ destinationBefore[0].end() : destinationTagIndex[0].start() ].count('.')
            #calculating score
            #maximum score is 1000
            #distance is substracted
            #for each sentence, 100 is substracted beacause if they are in different sentences their chance of being tag-data pair is less
            scoreBefore=1000-distanceBefore-(sentenceInBetween*100)

        #calculating score for PLACE match before the DESTINATION-TAG match
        if len(destinationAfter)>0:
            distanceAfter=destinationAfter[0].start()-destinationTagIndex[0].end()
            sentenceInBetween=emailContent[ destinationTagIndex[0].end() : destinationAfter[0].start() ].count('.')
            scoreAfter=1000-distanceAfter-(sentenceInBetween*100)

        #find which score is maximum
        if scoreBefore>0 or scoreAfter>0:
            #append the maximum score and corresponding destination match object as a pair to a list
            if scoreBefore>scoreAfter:
                nearestDestinationPairScore.append([scoreBefore,destinationBefore[1]])
            else:
                nearestDestinationPairScore.append([scoreAfter,destinationAfter[1]])

    #getting the corresponding PLACE value from the taggedIndices
    #maximum value of score from nearestDestinationPairScore is choosen as the data of interest
    try:
        dataIndex = nearestDestinationPairScore[getMaximumIndex(nearestDestinationPairScore,0)][1]
        destinationValue = taggedIndices[ dataIndex ][0].group()
        del taggedIndices[dataIndex]
    finally:
        return destinationValue.strip()

def setNewEmailInFile(email_text):
    file=open("./PATInExE Data/Inbox/new_mail.txt","w")
    file.write(email_text)
    file.close()

def extractInformationFromEmailFile():
    #reding new email content from Inbox
    new_email="./PATInExE Data/Inbox/new_mail.txt"
    with open(new_email, 'r',encoding='cp1252') as myfile:
        emailContent=re.sub(r'[\t\n]',' . ',myfile.read())

    #reading list of places from GlobalData
    places_list="./PATInExE Data/places_list.txt"
    with open(places_list,'r',encoding='cp1252') as myfile:
        listOfPlaces = [place.strip() for place in myfile if len(place.strip())>0]


    dataDictionary={}

    regularExpressions=[]
    regularExpressions.append([re.compile(r" [0-2]?[0-9]:[0-5][0-9] *([AaPpH][mMRr]s*)? "),"TIME"])
    regularExpressions.append([re.compile(r"(Scheduled Departure|Departs)"),"DEPART-TIME"])
    regularExpressions.append([re.compile(r" ([Dd]ate of [Jj]ourney|Date .) "),"DEPART-DATE"])
    regularExpressions.append([re.compile(r" [0-3]?[0-9][-/]?(Jan|Fe|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|([0-1]?[0-9]))[-/]?[12]?[0-9]?[0-9][0-9] "),"DATE"])
    regularExpressions.append([re.compile(r"[0-9]{10,12}"),"TICKET-ID"])
    regularExpressions.append([re.compile(r"( PNR No.? | PNR Number| Booking ID )"),"TICKET-ID-TAG"])
    regularExpressions.append([re.compile(r"(\+?)([0-9][0-9])?[^(A-Za-z0-9)][0-9]{3,3} ?[0-9] ?[0-9] ?[0-9]{5,5} "),"PHONE-NO"])
    regularExpressions.append([re.compile(r" Phone ",re.I),"PHONE-NO-TAG"])
    regularExpressions.append([re.compile(r" From "),"SOURCE-TAG"])
    regularExpressions.append([re.compile(r" To "),"DESTINATION-TAG"])
    regularExpressions.append([re.compile(r" | ".join(listOfPlaces)),"PLACE"])

    taggedIndices=[]
    for regularExpression in regularExpressions:
        for matchItem in re.finditer(regularExpression[0],emailContent):
            taggedIndices.append([matchItem,regularExpression[1]])

    taggedIndices=sorted(taggedIndices,key=getKeys)

    if classifyEmailFromFile()==True:
        if isCancelMail(emailContent):
            #cancel the entry corresponding to given TICKET-ID
            dataDictionary["STATUS"]="CANCELLED"
            dataDictionary["TICKET-ID"]=getTicketID(emailContent,taggedIndices)
        else:
            dataDictionary["STATUS"]="POTENTIAL"
            dataDictionary["DEPART-TIME"]=getDepartureTime(emailContent,taggedIndices)
            dataDictionary["DEPART-DATE"]=getDepartureDate(emailContent,taggedIndices)
            dataDictionary["TICKET-ID"]=getTicketID(emailContent,taggedIndices)
            dataDictionary["PHONE-NO"]=getPhoneNumber(emailContent,taggedIndices)
            dataDictionary["SOURCE"]=getJourneySource(emailContent,taggedIndices)
            dataDictionary["DESTINATION"]=getJourneyDestination(emailContent,taggedIndices)
    else:
        dataDictionary["STATUS"]="NON-POTENTIAL"

    return dataDictionary
