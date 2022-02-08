import json

dirPath = os.path.realpath(__file__)
if '\\' in dirPath:
    dirPath = dirPath.split('\\')
elif '/' in dirPath:
    dirPath = dirPath.split('/')
dirPath.pop()
temp = ""
for i in dirPath:
    temp += (f"{i}/")
dirPath = temp

runtime = {
	'dirPath': dirPath
}
del dirPath
del temp

assetData = {
	'weapons': {}
}


def loadAsset(assetName):
    print("Importing asset...")
    with open(f'{runtime['dirPath']}assets/{assetName}.json') as JSON:
    	data = json.load(JSON)

    loadAssetData(data)


def loadAssetData(data):

	for k, v in data.items():
		print(k, v)

load