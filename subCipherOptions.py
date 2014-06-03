# Run "findMatches" on a string of text with only letters and spaces
# to find all possible english text that can be gotten to using a substitution
# cypher on that text.
# Optional inputs: returnTree (boolean, default False). If True, the output
#                    is a tree of results, instead of a list
#                  saveFile (string, default None). If included, saves result
#                    to a file. If the result is a list, it will save one string
#                    per line. If a tree, it will save a JSON version of the tree

# Interesting example. Run on "PN PU GV WSJ TGBPT WL TPVK NOGN AOKV CWE OGDK
# KBISEJKJ NOK PTXWUUPHSK AOGNKDKZ ZKTGPVU OWAKDKZ PTXZWHGHSK TEUN HK NOK NZENO"
#
# Takes far too long on strings of several short words with no long words
# (For example "PN PU GV WSJ" takes an extremely long time.)
# The former examples is saved from this by matching long words first.


import json
import time

# Takes a list of words and builds a tree out of it
# Tree is implementes as a dict, where each leaf is the string that is the
# word there
# The word list it takes in needs to be in alphabetical order, and not have
# duplicates
def buildTree(wordList, depth = 0):
    # If we're at the last layer, return the word (should be unique)
    if len(wordList[0]) == depth:
        return wordList[0]

    tree = dict()
    # Go through each letter, and add a branch that is a tree of all
    # the words in that branch.
    numWords = len(wordList)
    done = False
    curBranch = None
    while wordList:
        # if we're not currently looking for a particular thing, start looking
        # for the current element of the first item, and initialize
        # the list of words to add to that branch
        if curBranch == None:
            curBranch = wordList[0][depth]
            branchWords = [wordList.pop(0)]
        
        # as long as appropriate element is the one we're looking for, add this
        # to the words in the new branch
        elif wordList[0][depth] == curBranch:
            branchWords.append(wordList.pop(0))
        # When we encounter a new one, create the branch and
        # add create that branch
        # TODO could be improved by creating a merge function, so the input
        # doesn't /need/ to be sorted
        else:
            tree[curBranch] = buildTree(branchWords, depth = depth+1)
            curBranch = None #Then reset what we're looking for and loop

    # When that while list finishes, we'll have one more branch to build
    if not (curBranch == None):
        tree[curBranch] = buildTree(branchWords, depth = depth+1)

    return tree
            

def createTemplate(s):
    return map(lambda x: list(x),s.split(' '))

def createWordList(trim = True):
    f = open("dictionary.txt","r")
    words = []
    for i in range(50):
        words.append([]) #Assume no words more than 50 characters long
    line = f.readline()
    while line:
        line = line[:-1] # Remove trailing newline
        words[len(line)].append(line) # Add word to correct bin by length
        line = f.readline()

    if trim:# remove trailing empty lists
        while True:
            if len(words[-1]) == 0:
                words = words[:-1]
            else:
                break
    return words


def checkTemplate(template, debug = False):
    startTime = time.time()
    # Set up initials so they can be reset after every discarded word
    fixedTemplateChars = []
    fixedTemplateChars_Init = []

    fixedMessageChars = []
    fixedMessageChars_Init = []

    fixedMapping = dict()
    fixedMapping_Init = dict()

    # reorder template to put longest words first
    template_tuples = []
    
    for i in range(len(template)):
        template_tuples.append([template[i],len(template[i]),i])

    # sort by length, descending
    template_tuples = sorted(template_tuples,
                             key = lambda x:x[1],
                             reverse = True)
    template = map(lambda x: x[0],template_tuples)

    
    words = createWordList()

    
    # Create a list of words that match each word individually
    possibleWords = []
    for wordTemplate in template:
        thisPossibleWords = []

        for word in words[len(wordTemplate)]:
            # undo information from the last word
            fixedTemplateChars = fixedTemplateChars_Init[:]
            fixedMessageChars = fixedMessageChars_Init[:]
            fixedMapping = fixedMapping_Init.copy()
            okayWord = True
            
            for i in range(len(word)):
                # check if letter is constrained
                if wordTemplate[i] in fixedTemplateChars:
                    if not word[i] == fixedMapping[wordTemplate[i]]:
                        okayWord = False
                        break # skip word if this letter doesn't match
                # if it's not constrained, but the letter is one we've used before
                # that's also bad
                elif word[i] in fixedMessageChars:
                    okayWord = False
                    break
                    
                # if it's unconstrained, now constrain it
                fixedMapping[wordTemplate[i]] = word[i]
                fixedMessageChars.append(word[i])
                fixedTemplateChars.append(wordTemplate[i])
                

            # if we've gotten past all the letters without a contradiction
            # add all possibilities using this word
            if okayWord:
                thisPossibleWords.append([word,
                                          fixedMapping])

        possibleWords.append(thisPossibleWords)

    setupDoneTime = time.time()

    # For every word in the template we'll be looking back at all previous valid
    # prefixes, and checking if we can add it

    validPrefixes = possibleWords[0] # all first words that work on their own


    for depth in range(1,len(template)):
        newPrefixes = []
        wordList =  map(lambda x: x[0],# don't need the mapping
                        possibleWords[depth])
        wordList.sort() # alpha order
        wordTree = buildTree(wordList)
        wordTemplate = template[depth]
        print("Checking matches for " + str(wordTemplate))

        for prefix in validPrefixes:

            if debug:
                print("\nNew prefix: " + prefix[0])
            fixedMap = prefix[1].copy()

            newPrefixes = newPrefixes + validNewPrefixes(wordTemplate,
                                                         fixedMap = fixedMap.copy(),
                                                         words = wordTree,
                                                         prefix = prefix[0])
                                                     
        # After we've checked all words at this layer against all previous
        # prefixes, update to use the new prefixes.
        validPrefixes = newPrefixes

    matchingDoneTime = time.time()

    retVal= []
    for i in range(len(validPrefixes)):
        validPrefixes[i] = validPrefixes[i][0].split(' ')
        blank = []
        for j in range(len(template)):
            blank.append([])
        retVal.append(blank)

    for i in range(len(validPrefixes)):
        for j in range(len(template)):
            originalInd = template_tuples[j][2]

            retVal[i][originalInd] = validPrefixes[i][j]

        retVal[i] = ' '.join(retVal[i])

    doneTime = time.time()

    print("Time to find individual word matches: " +
          str(setupDoneTime-startTime))
    print("Time to match words to each other: " +
          str(matchingDoneTime-setupDoneTime))
    print("Time to reformat output: " +
          str(doneTime - matchingDoneTime))
    
    # returning only the first part of each element
    return retVal

# Recursively searches a tree of possible next words
# Returns an array of new prefixes, including the mapping used for that prefix
# "words" is tree (implemented as a dict), with each leaf being the string that
# is that word
def validNewPrefixes(template, fixedMap, words, prefix):
    if len(template) == 0:
        # Need it inside extra array layer so when it gets added to another
        # array this becomes a single element in that array
        return [[prefix + ' ' +words,fixedMap]]

    if template[0] in fixedMap.keys():
        # If the first letter is constrained, follow only the branch
        # that the first letter of our template decodes to
        try:
            branchToFollow = words[fixedMap[template[0]]]
            return validNewPrefixes(template[1:],
                                    fixedMap = fixedMap.copy(),
                                    words = branchToFollow,
                                    prefix = prefix)
        except KeyError: #This happens if that branch doesn't exist
            return []

    # If the first letter isn't constrained, then we need to follow every
    # existing branch that hasn't already been used
    newPrefixes = []
    usedLetters = fixedMap.values()
    for branch in words.keys(): # follow remaining branches
        if not branch in usedLetters:
            newMap = fixedMap.copy()
            newMap[template[0]] = branch # add map information from first character
            newPrefixes = newPrefixes + validNewPrefixes(template[1:],
                                                         fixedMap = newMap,
                                                         words = words[branch],
                                                         prefix = prefix)

    return newPrefixes
                                                     
        

    

def findMatches(s, returnTree = False, saveFile = None):
    template = createTemplate(s)
    result = checkTemplate(template)
    if returnTree:
        result = buildTree(map(lambda x: x.split(' '),result))
    if saveFile:
        f = open(saveFile, 'w')
        if returnTree:
            f.write(json.dumps(result))
        else:
            f.writelines(map(lambda x: x+'\n',result))
        f.close()
        
    return result
