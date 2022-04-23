#!python3

import json
import os
from pathlib import Path

# The following txt file was created by copying all text from chapters 2 and 3 from the Foscam API PDF and pasted to a txt file.
# Turns out that the tables are not converted to text in any consistent way.
source_file = 'Foscam-IPCamera-CGI-User-Guide-AllPlatforms-2015.11.06.pdf.txt'

# Print some possible problems to stdout?
debug = False

def extract_all_between(after_text: str, before_text: str, lines, j: int, j_max: int):
    """
    Assumes the following text, starting on the j:th line in lines:
    ```
    after_text AAAA
    BBBB
    CCCC DDDD
    before_text EEEE
    ```
    or
    ```
    AAAA
    BBBB
    CCCC DDDD
    before_text EEEE
    ```
    or
    ```
    after_text AAAA BBBB CCCC DDDD before_text EEEE
    ```

    Returns "AAAA BBBB CCCC DDDD" and j where before_text is in lines
    """
    s = lines[j].find(after_text)
    e = lines[j].find(before_text)
    if s != -1:
        extracted_text = lines[j][(s+len(after_text))+1:]
    else:
        extracted_text = lines[j]
    if e != -1:
        e = extracted_text.find(before_text)
        extracted_text = extracted_text[:e]
    else:
        j += 1
        while j < j_max and not lines[j].startswith(before_text):
            extracted_text += lines[j].strip()
            j += 1
    return extracted_text, j


if __name__ == '__main__':
    full_path_of_this_script_dir = Path(os.path.realpath(__file__)).resolve().parent
    
    with open(Path(full_path_of_this_script_dir / source_file)) as f:
        lines = f.readlines()

    # Drop headers:
    lines = [l for l in lines if "All Platform" not in l]

    # Drop page footers:
    lines = [l for l in lines if "Copyright@" not in l]

    # Drop page headers:
    lines = [l for l in lines if "IPCamera CGI User Guide" not in l]

    # Drop some random lines:
    lines = [l for l in lines if "(20480~2097152)" not in l]
    
    # TODO: There are still some extra subheaders that should be dropped...

    # Parse all commands/methods:
    methods = []
    i = 0
    while i < len(lines):
        if not lines[i].startswith("Function"):
            i += 1
            continue
        cmd = lines[i-1]
        methods.append(cmd.rstrip())
        i += 1
    
    # Define generic options for boolean-type parameters:
    booleanParam = {
        "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
        "options" : {
            "false/disabled (0)" : 0,
            "true/enabled (1)" : 1,
        }
    }
    
    # Parse the params, based on the Example:
    commandJson = {}
    i = 0
    i_m = 0
    while i < len(lines) and i_m < len(methods):
        if not lines[i].startswith("Example"):
            i += 1     
            continue
        if i_m < len(methods)-1:
            example, i = extract_all_between("Example", methods[i_m+1], lines, i, len(lines))
        else:
            example, i = extract_all_between("Example", "EOF", lines, i, len(lines))

        all_params = example.replace("/cgi-bin/CGIProxy.fcgi?", "").replace(f"cmd={methods[i_m]}", "").replace("usr=admin", "").replace("pwd=", "").strip()
        if len(all_params.strip("&")) > 2:
            params = all_params.split("&")[1:]
            params_dict = {}
            boolean_params = []
            for param in params:
                key_value = param.split("=")
                if len(key_value) == 2:
                    paramKey = key_value[0].strip().replace('\n','')
                    paramExamplevalue = key_value[1].strip().replace('\n','')
                    params_dict[paramKey] = paramExamplevalue
                    
                    if paramKey[:2] == "is" or paramKey == "enable":
                        boolean_params.append(paramKey) # collect all params for which enabled/disabled options can be automatically added
                elif debug and key_value[0].strip() != "":
                    print(f"Failed to parse parameters of {methods[i_m]}: {key_value}")
        else:
            params_dict = None
            boolean_params = []
        
        if params_dict is not None and len(boolean_params) > 0:
            paramOptionsDict = {    # Add automatically dropdown options for all isEnable parameters
                param : booleanParam
                for param in boolean_params
            }
        else:
            paramOptionsDict = None
        
        p = {
            "ExampleParams" : params_dict,
            "paramOptions" : paramOptionsDict,
        }
        
        if not "not use" in methods[i_m]: # PDF contains some commands that are "not use"d ...  ignore them
            commandJson[methods[i_m]] = p

        i += 1
        i_m += 1
        
    
    # Parse the description and privilege:
    i = 0
    while i < len(lines):
        if not lines[i].startswith("Function"):
            i += 1     
            continue
        cmd = lines[i-1].strip()
        function, i = extract_all_between("Function", "privilege", lines, i, len(lines))
        privilege, i = extract_all_between("privilege", "Usage", lines, i, len(lines))

        if not "not use" in cmd: # PDF contains some commands that are "not use"d ...  ignore them
            commandJson[cmd]["Function"] = function.rstrip().replace('\n','')
            commandJson[cmd]["Privilege"] = privilege.rstrip().replace('\n','')
        i += 1


    #########################################################
    # MANUAL ADDITIONS AND CORRECTIONS TO THE commandJson:  #
    #########################################################
    #                                                       #
    #
    # The automatically parsed `commandJson` contains items
    # like below. They are manually appended or fixed below.
    # Especially `paramOptions` is None by default.
    #
    #  "setAlarmRecordConfig": {
    #      "ExampleParams": {
    #          "isEnablePreRecord": "1",
    #          "preRecordSecs": "5",
    #          "alarmRecordSecs": "30"
    #      },
    #      "paramOptions": {
    #          "isEnablePreRecord": {
    #              "optionsType": "dict",  # "list", or "dict" if the options have names
    #              "options": {
    #                  "false/disabled (0)": 0,
    #                  "true/enabled (1)": 1
    #              }
    #          }
    #      },
    #      "Function": "Set alarm record config",
    #      "Privilege": "admin"
    #  }
    #
    #
    
    streamTypeParam = {
        "optionsType" : "list", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
        "options" : [0,1,2,3]
    }
    
    resolutionParam = {
        "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
        "options" : {
            "QHD/1536p (9)" : 9,
            "FullHD/1080p (7)" : 7,
            "HD/720p (0)" : 0,
            "VGA/480p (3)" : 3,
            "VGA 4:3 (1)" : 1,
        }
    }
    
    commandJson["setSubVideoStreamType"] = {    # missing from PDF
        "ExampleParams": {
            "streamType": "0"
            },
        "Function": "Set the stream type of sub stream",
        "Privilege": "admin",
        "paramOptions": {
            "streamType": streamTypeParam
        }
    }
    
    commandJson["setMainVideoStreamType"]["paramOptions"] = { "streamType" : streamTypeParam } # add parameter options
    commandJson["setVideoStreamParam"]["paramOptions"] = { # add parameter options
        "streamType" : streamTypeParam,
        "resolution" : resolutionParam,
        "isVBR" : booleanParam,
        }
    commandJson["setSubVideoStreamParam"]["paramOptions"] = { # add parameter options
        "streamType" : streamTypeParam,
        "resolution" : resolutionParam, # do all resolutions work for sub stream too?
        "isVBR" : booleanParam,
        } 
    commandJson["getMainVideoStreamType"]["Function"] += ". The streamType can be 0,1,2 or 3. It is basically a settings profile where you can save the video encoding settings, and then easily switch between profiles. If you edit streamTypes other than the currently active (0 by default), you must remember to also setMainVideoStreamType to that number to take the new settings into use." # Add better explanation of the streamType which is not so much a type
    
    commandJson["setVideoStreamParam"]["Function"] += ". Good bitRates to try: 4194304, 2097152, 1048576, 524288, 262144, 131072 (or may have to be between 20480--2097152). Good frameRates: 20, 15, 10, 5. GOP (key frame interval): P frames between I frame, the suggested value is: X * frameRate, e.g. 40, 30, 20, 10." # Add help for parameters.
    
    timeSourceParam = {
        "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
        "options" : {
            "NTP (0)" : 0,
            "set time manually below (1)" : 1
        }
    }
    timeFormatParam = {
        "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
        "options" : {
            "12 h (0)" : 0,
            "24 h (1)" : 1
        }
    }
    dateFormatParam = {
        "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
        "options" : {
            "YYYY-MM-DD (0)" : 0,
            "DD/MM/YYYY (1)" : 1,
            "MM/DD/YYYY (2)" : 2,
        }
    }
    commandJson["setSystemTime"] = {    # Replace with better defaults
        "ExampleParams": {
            "timeSource": "0",
            "ntpServer": "Auto",
            "dateFormat": "0",
            "timeFormat": "1",
            "timeZone": "0",
            "isDst": "0",
            "dst": "0",
            "year": "2022",
            "mon": "1",
            "day": "6",
            "hour": "9",
            "minute": "35",
            "sec": "0"
        },
        "paramOptions": {
            "timeSource" : timeSourceParam,
            "timeFormat" : timeFormatParam,
            "dateFormat" : dateFormatParam,
            "isDst" : booleanParam
        },
        "Function": "Set system time. timeZone is the seconds between local time and GMT time. For example: timeZone=-7200 presents GMT+2 time (e.g. Finland), timeZone=3600 presents GMT-01:00, and timeZone=-3600 presents GMT+01:00",
        "Privilege": "admin"
    }
    
    privilegeParam = {
        "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
        "options" : {
            "Visitor (0)" : 0,
            "Operator (1)" : 1,
            "Administrator (2)" : 2,
        }
    }
    commandJson["addAccount"]["paramOptions"] = {
        "privilege" : privilegeParam
    }
    
    commandJson["setIpInfo"]["paramOptions"] = {
        "isDHCP" : booleanParam
    }
    commandJson["setIpInfo"]["ExampleParams"]["dns1"] = "8.8.8.8"
    commandJson["setIpInfo"]["ExampleParams"]["isDHCP"] = 1
    
    commandJson["setWifiSetting"]["Function"] += ". Give 'ssid' and 'psk'. Others you can usually ignore and leave as defaults."
    commandJson["setWifiSetting"]["ExampleParams"]["encryptType"] = 3   # Better example/default values
    commandJson["setWifiSetting"]["ExampleParams"]["authMode"] = 2
    commandJson["setWifiSetting"]["ExampleParams"]["ssid"] = "wifi_SSID"
    commandJson["setWifiSetting"]["ExampleParams"]["psk"] = "wifi_password"
    commandJson["setWifiSetting"]["paramOptions"] = {
        "isEnable" : booleanParam,
        "isUseWifi" : booleanParam,
        "encryptType" : {
            "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
            "options" : {
                "Open mode (0)" : 0,
                "WEP (1)" : 1,
                "WPA (2)" : 2,
                "WPA2 (3)" : 3,
                "WPA/WPA2 (4)" : 4,
            }
        }
    }
    
    commandJson["setSMTPConfig"]["ExampleParams"] = {   # errors in PDF: send --> sender and tls missing. Also add better defaults.
        "isEnable": "1",
        "server": "smtp.gmail.com",
        "port": "465",
        "isNeedAuth": "1",
        "user": "youraccount@gmail.com",
        "password": "your_gmail_account_app_password",
        "sender": "youraccount@gmail.com",
        "reciever": "youraccount@gmail.com,anotherreceiver@gmail.com",  # note: typo in API
        "tls": "1"
    }
    commandJson["setSMTPConfig"]["paramOptions"]["tls"] = {
        "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
        "options" : {
            "none (0)" : 0,
            "TLS (use this for Gmail) (1)" : 1,
            "STARTTLS (2)" : 2,
        }
    }
    commandJson["setSMTPConfig"]["Function"] = "Set mail config. Defaults work with Gmail. You have to enable 2-step verification for your Gmail account and then create an app password in Google account settings. Gmail probably also supports STARTTLS with port 587 or 25. For Hotmail use STARTTLS with port 587 or 25. Maximum length of password may be 16." # error in PDF

    commandJson["smtpTest"]["ExampleParams"] = {   # Better defaults
        "smtpServer": "smtp.gmail.com",
        "port": "465",
        "isNeedAuth": "1",
        "user": "youraccount@gmail.com",
        "password": "your_gmail_account_app_password",
        "sender": "youraccount@gmail.com"
    }
    
    modeParam = {
        "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
        "options" : {
            "PASV mode (0)" : 0,
            "PORT mode (1)" : 1,
        }
    }
    commandJson["setFtpConfig"]["paramOptions"] = { "mode" : modeParam }
    commandJson["testFtpServer"]["paramOptions"] = { "mode" : modeParam }
    
    commandJson["setP2PEnable"]["ExampleParams"]["enable"] = 0  # better default
    
    ddnsServerParam = {
        "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
        "options" : {
            "Factory DDNS (0)" : 0,
            "Oray (1)" : 1,
            "3322 (2)" : 2,
            "no-ip (3)" : 3,
            "dyndns (4)" : 4,
        }
    }
    commandJson["setDDNSConfig"]["paramOptions"]["ddnsServer"] = ddnsServerParam
    commandJson["setDDNSConfig"]["ExampleParams"]["isEnable"] = 0  # better default
    
    
    commandJson["setSnapConfig"]["paramOptions"] = {
        "snapQuality" : {
            "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
            "options" : {
                "Low quality (0)" : 0,
                "Normal quality (1)" : 1,
                "High quality (2)" : 2,
            }
        },
        "saveLocation" : {
            "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
            "options" : {
                "Save to sd card (0)" : 0,
                "Not in use now (1)" : 1,
                "Upload to FTP (2)" : 2,
            }
        }
    }
    
    commandJson["setPwrFreq"]["ExampleParams"]["freq"] = 2  # default outdoor cameras
    commandJson["setPwrFreq"]["paramOptions"] = {
        "freq" : {
            "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
            "options" : {
                "60 Hz (0)" : 0,
                "50 Hz (1)" : 1,
                "Outdoor mode (2)" : 2,
            }
        }
    }
    
    commandJson["setInfraLedConfig"]["ExampleParams"]["mode"] = 0
    commandJson["setInfraLedConfig"]["paramOptions"] = {
        "mode" : {
            "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
            "options" : {
                "Auto mode (0)" : 0,
                "Manual mode (1)" : 1,
            }
        }
    }
    commandJson["openInfraLed"]["Function"] += ". The 'setInfraLedConfig' mode must be 1 (manual) for this to work."
    commandJson["closeInfraLed"]["Function"] += ". The 'setInfraLedConfig' mode must be 1 (manual) for this to work."

    commandJson["setScheduleSnapConfig"]["ExampleParams"]["isEnable"] = "0"
    commandJson["setScheduleSnapConfig"]["Function"] += ". To figure out the values for schedule parameters, you can possibly use the (motion detection) schedule table in the 'Detector' view."
    
    commandJson["setMotionDetectConfig"]["Function"] += ". NOTE: The motion detection area and schedule and others must always be included, even if you for example only want to toggle (enable) the 'isEnable'. For the area params '1023' and for schedule params '281474976710655' mean that the motion detection is always enabled for the entire image area. You can use the checkbox tables and their 'Apply' buttons above to input the parameters without manually calculating the bitmaps. 'snapInterval' means the interval time to snap picture again. 'triggerInterval' means the time after which the motion detect alarm can trigger again after a motion detection has happened (+ 5 seconds)."
    commandJson["setMotionDetectConfig"]["ExampleParams"] = {
        "isEnable": "1",
        "linkage": "14",
        "snapInterval": "2",
        "sensitivity": "1",
        "triggerInterval": "5",
        "isMovAlarmEnable": "1",
        "isPirAlarmEnable": "1",
        "area0": "1023",
        "area1": "1023",
        "area2": "1023",
        "area3": "1023",
        "area4": "1023",
        "area5": "1023",
        "area6": "1023",
        "area7": "1023",
        "area8": "1023",
        "area9": "1023",
        "schedule0": "281474976710655",
        "schedule1": "281474976710655",
        "schedule2": "281474976710655",
        "schedule3": "281474976710655",
        "schedule4": "281474976710655",
        "schedule5": "281474976710655",
        "schedule6": "281474976710655"
    }
    sensitivityParam = {
        "Low (0)" : 0,
        "Medium (1)" : 1,
        "High (2)" : 2,
        "Lower (3)" : 3,
        "Lowest (4)" : 4,
    }
    commandJson["setMotionDetectConfig"]["paramOptions"]["sensitivity"] = {
        "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
        "options" : sensitivityParam
    }
    
    commandJson["setAudioAlarmConfig"]["paramOptions"]["sensitivity"] = {
        "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
        "options" : sensitivityParam
    }
    commandJson["setAudioAlarmConfig"]["Function"] = "Set the sound detection config. For 'sensitivity' probably only 0, 1 and 2 work. 'Linkage' and 'schedule' work the same way as with setMotionDetectConfig above, so you can use the table above to figure out the correct values."
    commandJson["setAudioAlarmConfig"]["ExampleParams"]["linkage"] = 14
    for i in range(7):
        commandJson["setAudioAlarmConfig"]["ExampleParams"]["schedule"+str(i)] = 281474976710655
    
    commandJson["setRecordPath"]["paramOptions"] = {
        "path" : {
            "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
            "options" : {
                "SD card (0)" : 0,
                "FTP server (2)" : 2,
                "SD card and cloud (3)" : 3,
            }
        }
    }
    commandJson["setRecordPath"]["ExampleParams"]["path"] = 2
    commandJson["setRecordPath"]["Function"] += ". How to read the response: 'setResult': 0 success, -1 Sd card is not exist, -2 Share direction is not set, -3 Not enough space, -4 Param error, -5 Param recording."
    
    commandJson["setScheduleRecordConfig"]["Function"] += ". (This can be disabled if you only want to record a video clip when motion is detected.) The 'schedule' parameters work the same way as with setMotionDetectConfig, so you can possibly use the table under the 'Detector' category to figure out the correct values."
    commandJson["setScheduleRecordConfig"]["ExampleParams"]["isEnable"] = 0
    for i in range(7):
        commandJson["setScheduleRecordConfig"]["ExampleParams"]["schedule"+str(i)] = 281474976710655
    
    commandJson["setScheduleRecordConfig"]["paramOptions"]["recordLevel"] = {
        "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
        "options" : {
            "Level for drop frame, 30/30 (0)" : 0,
            "24/30 (1)" : 1,
            "15/30 (2)" : 2,
            "8/30 (3)" : 3,
            "4/30 (4)" : 4,
            "1/30 (5)" : 5,
        }
    }
    commandJson["setScheduleRecordConfig"]["paramOptions"]["spaceFullMode"] = {
        "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
        "options" : {
            "Overwrite the oldest video and continue recording (0)" : 0,
            "Stop recording (1)" : 1,
        }
    }
    
    commandJson["setDeFrameLevel"]["paramOptions"] = {
        "level" : {
            "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
            "options" : {
                "Disable the status of enhance (0)" : 0,
                "Enable the status of enhance (1)" : 1,
            }
        }
    }
    
    commandJson["setCloudConfig"]["ExampleParams"]["isEnable"] = 0
    commandJson["setCloudConfig"]["ExampleParams"]["cloudServer"] = 1
    commandJson["setCloudConfig"]["ExampleParams"]["code"] = "Authorization code from server"
    cloudServerParam = {
        "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
        "options" : {
            "Dropbox (1)" : 1,
            "Baidu (2)" : 2,
        }
    }
    commandJson["setCloudConfig"]["paramOptions"]["cloudServer"] = cloudServerParam
    
    commandJson["selectCloudServer"]["ExampleParams"]["isEnable"] = 0
    commandJson["selectCloudServer"]["paramOptions"]["cloudServer"] = cloudServerParam
    
    commandJson["getCloudToken"]["paramOptions"]["cloudServer"] = cloudServerParam
    commandJson["getCloudToken"]["Function"] += ". Call this cgi, then call getCloudConfig 10s later, find accessToken"
    

    commandJson["getCloudQuota"]["paramOptions"]["cloudServer"] = cloudServerParam
    commandJson["getCloudQuota"]["Function"] += ". Call this cgi, then call getCloudConfig 10s later, find accessToken"

    commandJson["testCloudServer"]["paramOptions"]["cloudServer"] = cloudServerParam
    commandJson["testCloudServer"]["Function"] += ". Call this cgi, then call getCloudConfig 10s later, find accessToken"
    
    commandJson["exportConfig"]["Function"] += ". After calling this command, you can get the config file by visiting the following address: /configs/export/configs.bin"
    
    commandJson["ImportConfig"]["Function"] += ". See the Foscam API PDF documentation how this actually works. This button probably does not work."
    commandJson["FwUpgrade"]["Function"] += ". See the Foscam API PDF documentation how this actually works. This button probably does not work."
    
    commandJson["restoreToFactorySetting"]["Function"] += ". WARNING! This will erase all settings in camera and you may lose connection to the camera, especially wireless. Also remember to close the new opened tab so that you don't later accidentally reload that tab, performing the erase again. (For now clicking the button only shows the URL - copy and paste it manually to the address bar and send.)"
    commandJson["restoreToFactorySetting"]["ExampleParams"] = None
    
    commandJson["setPTZSpeed"]["paramOptions"] = {
        "speed" : {
            "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
            "options" : {
                "Slowest (Opticam: Fastest) (0)" : 0,
                "Slow (Opticam: Fast) (1)" : 1,
                "Normal speed (2)" : 2,
                "Fast (Opticam: Slow) (3)" : 3,
                "Fastest (Opticam: Slowest) (4)" : 4,
            }
        }
    }
    
    commandJson["getPTZPresetPointList"]["Function"] += ". The device can support at most 16 preset points. There are four default points: LeftMost, RightMost, TopMost, BottomMost."
    
    commandJson["ptzAddPresetPoint"]["ExampleParams"] = {
        "name": "1",
    } # incorrectly parsed from the pdf for some reason
    commandJson["ptzAddPresetPoint"]["Function"] += ". The preset point position will be the current PT position. Third-party applications usually use simply numbers (e.g. 1 or 5) as the names. If a preset with the given name already exists, you may have to delete it first (see ptzDeletePresetPoint)."
    
    commandJson["setPTZSelfTestMode"]["paramOptions"] = {
        "mode" : {
            "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
            "options" : {
                "No selftest (0)" : 0,
                "Normal selftest (1)" : 1,
                "After selftest, goto presetpoint set with setPTZPrePointForSelfTest (2)" : 2,
            }
        }
    }
    commandJson["ptzDeletePresetPoint"]["Function"] += ". If the preset is defined as the preset to go to after boot, you may have to change that definition to something else first (see setPTZPrePointForSelfTest)."
    
    commandJson["setPTZPrePointForSelfTest"]["Function"] += ". This setting defines the position of PTZ after the camera boots. Set the preset name with this, and enable mode 2 with 'setPTZSelfTestMode'."
    commandJson["setPTZPrePointForSelfTest"]["ExampleParams"] = {
        "name": "1",
    } # incorrectly parsed from the pdf for some reason

    commandJson["getPTZPrePointForSelfTest"]["ExampleParams"] = None # incorrectly parsed from the pdf for some reason

    commandJson["setZoomSpeed"]["paramOptions"] = {
        "speed" : {
            "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
            "options" : {
                "Slow (or Fast?) (0)" : 0,
                "Normal (1)" : 1,
                "Fast (or Slow?) (2)" : 2,
            }
        }
    }
    
    commandJson["ptzGetCruiseMapInfo"]["ExampleParams"] = {
        "name": "1",
    } # incorrectly parsed from the pdf for some reason
    
    commandJson["ptzSetCruiseMap"]["Function"] += ". Our device can support at most 8 preset point one cruise map. The 'name' is the name of the cruise map. The 'point' parameters are preset names."
    
    commandJson["getCruiseTime"]["Function"] = "Get time for continue cruise. NOTE: The API PDF starting from here is full of errors and weird things, so the rest of the cruise commands probably contain some errors." # typo in pdf
    commandJson["getCruiseTimeCustomed"]["Function"] = "Get time for customed continue cruise." # typo in pdf

    commandJson["setCruiseTimeCustomed"]["paramOptions"] = {
        "customed" : booleanParam
    }
    
    commandJson["setCruiseCtrlMode"]["paramOptions"] = {
        "mode" : {
            "optionsType" : "dict", # "list", or "dict" if the options have names: {"option1DisplayName" : "option1"}
            "options" : {
                "By time (0)" : 0,
                "By loop count (1)" : 1,
            }
        }
    }
    
    commandJson["getCruisePrePointLingerTime"]["ExampleParams"] = {
        "name": "test",
    } # incorrectly parsed from the pdf for some reason
    
    commandJson["snapPicture2"]["Function"] += ". Get a jpg still image from the camera."
    
    commandJson["importConfig"] = commandJson["ImportConfig"] # which one is correct?
    commandJson["fwUpgrade"] = commandJson["FwUpgrade"] # which one is correct?
    
    commandJson["focusNear"] = {    # missing from PDF
        "ExampleParams": None,
        "Function": "Focus near.",
        "Privilege": "operator",
        "paramOptions": None
    }
    commandJson["focusFar"] = {    # missing from PDF
        "ExampleParams": None,
        "Function": "Focus far.",
        "Privilege": "operator",
        "paramOptions": None
    }
    commandJson["focusStop"] = {    # missing from PDF
        "ExampleParams": None,
        "Function": "Stop the focusing motor.",
        "Privilege": "operator",
        "paramOptions": None
    }
    
    #                                                       #
    #########################################################
    #########################################################


    ## Save the commandJson as json:
    #with open(Path(full_path_of_this_script_dir / "FoscamApiAutoscraped.json"), 'w') as fp:
    #    json.dump(commandJson, fp, indent=4)
    
    # Create the index.html by replacing a placeholder in the template-html:
    commandJsonString = json.dumps(commandJson, sort_keys=False, indent=4)
    
    with open(Path(full_path_of_this_script_dir / "index_template.html")) as f:
        templateHtml = f.read()
        
    finalHtml = templateHtml.replace("{COMMANDJSON_PLACEHOLDER}", commandJsonString)
    
    finalPathInParentDir = Path(full_path_of_this_script_dir.parent / 'index.html')
    print(f"Writing final HTML to {finalPathInParentDir}")
    with open(finalPathInParentDir, 'w') as fp:
        fp.write(finalHtml)

