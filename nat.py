import requests
import re
import os
import sys
import time
from datetime import datetime

def parseHTML(content):
    """
    Parse the HTML content to extract NAT tracks information
    """
    tracks = []
    validityPeriods = []
    
    # Find all validity periods (OCT 13/1130Z TO OCT 13/1900Z)
    validityPattern = r'([A-Z]{3})\s+(\d{1,2})/(\d{4})Z\s+TO\s+([A-Z]{3})\s+(\d{1,2})/(\d{4})Z'
    validityMatches = re.findall(validityPattern, content)
    
    for match in validityMatches:
        startMonth, startDay, startTime, endMonth, endDay, endTime = match
        validityPeriods.append({
            'start': {'month': startMonth, 'day': int(startDay), 'time': int(startTime)},
            'end': {'month': endMonth, 'day': int(endDay), 'time': int(endTime)}
        })
    
    # Find all track definitions (A RESNO 56/20 57/30...)
    trackPattern = r'^([A-Z])\s+(.+?)(?=EAST LVLS|$)'
    lines = content.split('\n')
    
    currentValidity = None
    for i, line in enumerate(lines):
        # Check if we're entering a new validity period
        if 'TRACKS FLS' in line:
            if validityPeriods:
                currentValidity = validityPeriods[0]
                validityPeriods.pop(0)
        
        # Look for track definitions
        if len(line) > 0 and line[0].isalpha() and line[0].isupper():
            match = re.match(r'^([A-Z])\s+(.+)', line.strip())
            if match and currentValidity:
                trackId = match.group(1)
                waypointsStr = match.group(2).strip()
                
                # Extract waypoints (names and coordinates)
                waypoints = []
                tokens = waypointsStr.split()
                for token in tokens:
                    # Check if it's a coordinate (contains /)
                    if '/' in token:
                        waypoints.append(token)
                    # Or a named waypoint (5-6 characters, alphanumeric)
                    elif re.match(r'^[A-Z0-9]{5,6}$', token):
                        waypoints.append(token)
                
                if len(waypoints) >= 2:  # Only add if we have at least 2 waypoints
                    tracks.append({
                        'id': trackId,
                        'waypoints': waypoints,
                        'validity': currentValidity
                    })
    
    return tracks

def isCurrentlyValid(validity):
    """
    Check if a NAT track is currently valid based on validity period
    """
    months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    now = time.gmtime()
    currentMonth = months[now.tm_mon - 1]
    currentDay = now.tm_mday
    currentTime = now.tm_hour * 100 + now.tm_min
    
    start = validity['start']
    end = validity['end']
    
    # Simple check (assumes same month for simplicity)
    if start['month'] == currentMonth and end['month'] == currentMonth:
        if start['day'] <= currentDay <= end['day']:
            if currentDay == start['day']:
                return currentTime >= start['time']
            elif currentDay == end['day']:
                return currentTime < end['time']
            else:
                return True
    
    return False

def getNATS():
    """
    Download and parse NAT tracks from FAA website
    """
    print("Connecting to FAA NAT server...")
    
    # Try multiple URLs and methods
    urls = [
        "https://notams.aim.faa.gov/nat.html",
        "https://www.notams.faa.gov/common/nat.html"
    ]
    
    # Headers to simulate a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    content = None
    lastError = None
    
    for url in urls:
        print(f"Trying: {url}")
        for attempt in range(3):  # 3 attempts per URL
            try:
                print(f"  Attempt {attempt + 1}/3...", end=" ")
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=30,  # Increased timeout
                    verify=True  # SSL verification
                )
                response.raise_for_status()
                content = response.content.decode("UTF-8")
                print("Success!")
                break
            except requests.exceptions.SSLError as e:
                print("SSL Error, trying without verification...")
                try:
                    response = requests.get(url, headers=headers, timeout=30, verify=False)
                    response.raise_for_status()
                    content = response.content.decode("UTF-8")
                    print("Success!")
                    break
                except Exception as e2:
                    lastError = str(e2)
                    print(f"Failed: {e2}")
            except requests.exceptions.Timeout:
                lastError = "Connection timeout"
                print("Timeout!")
                time.sleep(2)  # Wait before retry
            except requests.exceptions.RequestException as e:
                lastError = str(e)
                print(f"Failed: {e}")
                time.sleep(2)
        
        if content:
            break
    
    if not content:
        print(f"\nScript couldn't download necessary data.")
        print(f"Last error: {lastError}")
        print("\nPossible solutions:")
        print("1. Check your internet connection")
        print("2. Check if a firewall/antivirus is blocking the connection")
        print("3. Try running the script with administrator privileges")
        print("4. The FAA server might be temporarily down")
        input("\nPress ENTER to exit")
        raise SystemExit()
    
    try:
        print("\nParsing NAT tracks...")
        allTracks = parseHTML(content)
        
        if not allTracks:
            print("Warning: No tracks found in the downloaded data.")
            print("The website format might have changed.")
            input("Press ENTER to exit")
            raise SystemExit()
        
        # Filter only currently valid tracks
        validTracks = []
        latestValidUntil = 0
        
        for track in allTracks:
            if isCurrentlyValid(track['validity']):
                validTracks.append(track)
                endTime = track['validity']['end']['time']
                if endTime > latestValidUntil:
                    latestValidUntil = endTime
        
        if len(validTracks) == 0:
            print("No NATs are active at the moment.")
            print(f"Found {len(allTracks)} tracks total, but none are currently valid.")
            input("Press ENTER to exit")
            raise SystemExit()
        
        print(f"Found {len(validTracks)} active NAT track(s).")
        return validTracks, latestValidUntil
    
    except Exception as e:
        print(f"\nAn error occurred while parsing NATs: {e}")
        print("\nThe website format might have changed.")
        input("Press ENTER to exit")
        raise SystemExit()

def getAuroraPath():
    """
    Get or prompt for Aurora sectorfiles path
    """
    if getattr(sys, 'frozen', False):
        absolute_path = os.path.dirname(sys.executable)
    elif __file__:
        absolute_path = os.path.dirname(__file__)
    
    auroraPathFile = absolute_path + "/path.txt"
    
    if os.path.isfile(auroraPathFile):
        file = open(auroraPathFile, "r")
        auroraPath = file.read()
        file.close()
    else:
        auroraPath = input('Paste "Aurora" folder path: ').rstrip("\\")
        while not os.path.isdir(auroraPath):
            print("Invalid path. Please make sure you have pasted the correct path to the Aurora folder.")
            auroraPath = input('Paste "Aurora" folder path: ').rstrip("\\")
        
        auroraPath = auroraPath + "\\SectorFiles\\Include\\CA\\CZQX\\"
        
        if not os.path.isdir(auroraPath):
            print("The CA sectorfile (CZQX) was not found.")
            print("\nYou MUST download the 'CA - Gander/Shanwick OCC (Latest)' sectorfile.")
            input("Press ENTER to exit")
            raise SystemExit()
        else:
            file = open(auroraPathFile, "w")
            file.write(auroraPath)
            file.close()
            print("Created file with Aurora path in this directory: " + auroraPathFile + "\n")
    
    return auroraPath

def getAuroraFixes(auroraPath):
    """
    Read existing fixes from Aurora sectorfile
    """
    auroraFixes = []
    fixesPath = os.path.join(auroraPath, "fixes.fix")
    
    if not os.path.exists(fixesPath):
        print(f"Warning: fixes.fix not found at {fixesPath}")
        return auroraFixes
    
    with open(fixesPath, 'r') as file:
        data = file.read().split("\n")
    
    for fixInfo in data:
        if "//" not in fixInfo and fixInfo != "":
            fixInfo = fixInfo.split(";")
            if len(fixInfo) > 0:
                auroraFixes.append(fixInfo[0])
    
    return auroraFixes

def printInfo(usedNATS, validUntil):
    """
    Print information about added NATs
    """
    print("\nAdded NATs:")
    for nat in usedNATS:
        print("\tNAT " + nat)
    
    if validUntil > 0:
        validUntilStr = str(validUntil).zfill(4)
        print("To be updated after: " + validUntilStr[0:2] + ":" + validUntilStr[2:4] + "Z")

def appendToFile(updatedFile, auroraPath):
    """
    Write updated NATs to Aurora highairway file
    """
    highairwayPath = os.path.join(auroraPath, "highairway.awh")
    with open(highairwayPath, 'w') as file:
        file.write(updatedFile)

def addNATS(tracks):
    """
    Format NAT tracks for Aurora sectorfile
    """
    updatedFile = ""
    usedNATS = []
    usedFixes = []
    
    for track in tracks:
        ident = track['id']
        usedNATS.append(ident)
        waypoints = track['waypoints']
        
        labeled = False
        secondCol = "NAT" + ident
        
        for waypoint in waypoints:
            if not labeled:
                updatedFile += "L;" + ident + ";" + waypoint + ";" + waypoint + ";\n"
                labeled = True
            
            # Check if it's a coordinate or named fix
            if '/' in waypoint:
                # It's a coordinate
                newFix = ""
                coord = ""
                coordArr = waypoint.split("/")
                
                # Handle different coordinate formats
                if len(coordArr[0]) == 2:
                    # Format: 56/20 -> 5620N
                    coord = coordArr[0] + coordArr[1] + "N"
                    newFix = coord + ";N0" + str(coordArr[0]) + ".00.00.000;W0" + str(coordArr[1]) + ".00.00.000;"
                else:
                    # Format: 5530/30 -> H5530
                    coord = "H" + coordArr[0][0:2] + coordArr[1]
                    newFix = coord + ";N0" + str(coordArr[0][0:2]) + "." + str(coordArr[0][2:4]) + ".00.000;W0" + str(coordArr[1]) + ".00.00.000;"
                
                usedFixes.append(newFix)
                updatedFile += "T;" + secondCol + ";" + coord + ";" + coord + ";\n"
            else:
                # It's a named fix
                updatedFile += "T;" + secondCol + ";" + waypoint + ";" + waypoint + ";\n"
                usedFixes.append(waypoint)
    
    return usedFixes, updatedFile, usedNATS

def verifyMissingFixes(auroraFixes, usedFixes, auroraPath):
    """
    Check for missing fixes and add them to Aurora sectorfile
    """
    manualFixes = []
    added = False
    fixesPath = os.path.join(auroraPath, "fixes.fix")
    
    with open(fixesPath, 'a') as file:
        for fix in usedFixes:
            splittedFix = str(fix).split(";")
            if splittedFix[0] not in auroraFixes:
                if not added:
                    print("\nFixes that were added:")
                    added = True
                
                if len(splittedFix) > 1:
                    print("\t" + splittedFix[0])
                    file.write(fix + "\n")
                else:
                    manualFixes.append(splittedFix[0])
    
    if not added:
        print("\nNo additional fixes were added.")
    
    if manualFixes:
        print("\nFixes that have to be added manually:")
        for fix in manualFixes:
            print("\t" + fix)

def main():
    """
    Main function
    """
    print("=" * 50)
    print("Aurora NAT Updater v3.0")
    print("\n1.0 by 609402 - Dawid\n2.0 by 598172 - Santiago\n3.0 by 200696 - Joey")
    print("=" * 50)
    print()
    
    auroraPath = getAuroraPath()
    auroraFixes = getAuroraFixes(auroraPath)
    tracks, validUntil = getNATS()
    usedFixes, updatedFile, usedNATS = addNATS(tracks)
    printInfo(usedNATS, validUntil)
    appendToFile(updatedFile, auroraPath)
    verifyMissingFixes(auroraFixes, usedFixes, auroraPath)
    
    print("\n" + "=" * 50)
    print("Make sure to have downloaded the latest 'CA - Gander/Shanwick OCC (Latest)' sectorfile.")
    print("Update completed successfully!")
    print("=" * 50)
    input("\nPress ENTER to exit")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        input("Press ENTER to exit")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        input("Press ENTER to exit")