#maybe a little long
def processeffect(value):
    if value == 'True':
        return True
    elif value == 'False':
        return False
    else:
        raise ValueError


#convert from string to  float(value)
def process(value):
    try:
        float(value)
    except ValueError, e:
        return None
    else:
        return float(value)


def getPart(aData,aIndex):
    aPart=[]
    print aIndex
    for i in range(len(aIndex)):
        aPart.append(aData[aIndex[i]])
    return aPart

def getNextIndexArray(aIndex, max):
    print len(aIndex)
    for i in range(len(aIndex)):
        if(aIndex[i] < max):
			aIndex[i] += 1
			return aIndex
        else:
            for j in range(i+1,len(aIndex)):
				if(aIndex[j] < max):
					aIndex[j] += 1
					for k in  range(j-1,-1,-1):
						aIndex[k] = 0
					return aIndex
	return []

def combInArrayDup(aData, n):
	aResult = []
	aIndex = []
	for i in range(n):
		aIndex.append(0)
	iMax = len(aData) - 1
	while True:
		if(aIndex == []):
			break
		aResult.append(getPart(aData,aIndex))
		aIndex = getNextIndexArray(aIndex, iMax)
	return aResult

def sim_pearson(p1,p2):
    n1=len(p1)
    n2=len(p2)
    if n1!=n2:
        return 0
    sum1=sum(p1)
    sum2=sum(p2)
    sum1Sq=sum([pow(item) for item in p1])
    sum2Sq=sum([pow(item) for item in p2])
    pSum=sum([p1[i]*p2[i] for i in range(n1)])
    num=pSum-(sum1*sum2)/n1
    den=sqrt((sum1Sq-pow(sum1,2)/n)*(sum2Sq-pow(sum2,2)/n))
    if den==0: return 0
    r=num/den
    return r

# Returns the Pearson correlation coefficient for p1 and p2
def sim_pearson(prefs,p1,p2):
# Get the list of mutually rated items
    si={}
    for item in prefs[p1]:
        if item in prefs[p2]: si[item]=1
    # if they are no ratings in common, return 0
    if len(si)==0: return 0
   # Sum calculations
    n=len(si)

  # Sums of all the preferences
    sum1=sum([prefs[p1][it] for it in si])
    sum2=sum([prefs[p2][it] for it in si])
  # Sums of the squares

    sum1Sq=sum([pow(prefs[p1][it],2) for it in si])
    sum2Sq=sum([pow(prefs[p2][it],2) for it in si])

  # Sum of the products
    pSum=sum([prefs[p1][it]*prefs[p2][it] for it in si])

  # Calculate r (Pearson score)
    num=pSum-(sum1*sum2/n)
    den=sqrt((sum1Sq-pow(sum1,2)/n)*(sum2Sq-pow(sum2,2)/n))
    if den==0: return 0
    r=num/den
    return r



