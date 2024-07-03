from enum import Enum
import json
import os
import time
import jsonToQml

import pathvalidate

class Dumbledore:
    class Stage(Enum): 
        Start = -1
        Name = 0
        Version = 1
        ReadsScore = 2
        WritesScore = 3
        SavePath = 4
        ExecutablePath = 5
        OptionsExplanation = 6
        OptionsType = 8
        OptionsCLA = 9
        OptionsPrompt = 10
        OptionsValuesCombo = 11
        OptionsDefaultValue = 12        
        OptionsConfirm = 13
        OptionsAgain = 14
        Generate = 15
        GenerateAskFilePath = 16
        End = 17

    def __init__(self):
        self.currentStage = self.Stage['Start']
        self.memory = Remembrall()
        self.currentOption = None

    def print_progress_bar(self):
        totalStages = 8
        currentStage = self.currentStage.value
        if self.currentStage.value >= 6 and self.currentStage.value <= 14:
            currentStage = 6
        if self.currentStage == self.Stage.Generate or self.currentStage == self.Stage.GenerateAskFilePath:
            currentStage = 7
        if self.currentStage == self.Stage.End:
            currentStage = 8

        string = f"[{"".join(['#' for i in range(0, currentStage)])}{"".join(['-' for i in range(0, totalStages-currentStage)])}] {int(100*(float(currentStage)/float(totalStages)))}%"
        print(string)

    def print_already_added_options(self):
        if len(self.memory.options) == 0: return
        print("Already added items:")
        for i, item in enumerate(self.memory.options):
            print(f"{i + 1} - \"--{item.cla}\" {type(item)}")

    def print_about_current_option(self):
        print("Current option being added:")
        if self.currentOption is not None:
            t = ""
            match type(self.currentOption):
                case jsonToQml.Options.TextField: t = "TextField"
                case jsonToQml.Options.CheckBox: t = "CheckBox"
                case jsonToQml.Options.ComboBox: t = "ComboBox"
                case jsonToQml.Options.FileDialog: t = "FileDialog"

            print(f"Type: {t}")
        if self.currentOption.cla != "":
            print(f"Command-line argument: {self.currentOption.cla}")
        if self.currentOption.prompt != "":
            print(f"Prompt: {self.currentOption.prompt[:15]}")
        if type(self.currentOption) is jsonToQml.Options.ComboBox:
            if self.currentOption.values != []:
                print(f"Values: {self.currentOption.values}")
        if self.currentOption.defaultValue != "":
            print(f"Default value: {self.currentOption.defaultValue}")

    def print_prompt(self):
        match self.currentStage:
            case self.Stage.Start:
                print(f"Welcome to the Wizard. Let's get you started with creating the backbone of your plugin.\nPress ENTER to continue")

            case self.Stage.Name:
                print(f"What would you like to call your plugin? (max 20 chars)")

            case self.Stage.Version:
                print(f"What version of your plugin is this? (leave empty for default)")

            case self.Stage.ReadsScore:
                print(f"Does your process need to read the current score that is open?\n\tSaying yes means that the current score is stored as MusicXML file and then passed as a command-line argument to your script.\ny/n")

            case self.Stage.WritesScore:
                print(f"Does your process need to load the result of your processing?\n\tSaying yes means that the plugin loads the output MusicXML file from your script.\ny/n")

            case self.Stage.SavePath:
                print(f"Your script wants to read the current score. Where do you want to store this temp file?\n\tIf left empty, a default value of \"./temp/temp\" is chosen.\n\tRelative file paths are only partially supported. A leading . is translated to the folder in which the .qml file will be placed in. Take this into account with how you structure the directory.")
                print(f"PLEASE ENSURE THE FORMAT IS: \"./xxx/xxx/nameOfFile\" WITHOUT AN EXTENSION, this will be auto-filled in as .mxl")

            case self.Stage.ExecutablePath:
                print(f"What is the path to the script you want to call\n\tRelative file paths are only partially supported. A leading . is translated to the folder in which the .qml file will be placed in. Take this into account with how you structure the directory.")

            case self.Stage.OptionsExplanation:
                print(f"Now it's time to define the interfaces for selecting command-line arguments for the call to your script.\nIn this step, for each command-line argument you can select an appropriate type of UI element for your users to interact with.")
                print(f"Each UI element will correspond to one command-line argument for the call to your script.")
                print(f"Press ENTER to proceed.")

            case self.Stage.OptionsType:
                self.print_already_added_options()
                print(f"What kind of menu would you like to add?\n1. TextField\n2. CheckBox\n3. ComboBox\n4. FileDialog\n5. Finish adding UI elements")

            case self.Stage.OptionsCLA:
                self.print_about_current_option()
                print(f"What command-line argument do you want this to correspond to?\nDo not forget to add a '-' or '--' in front.")

            case self.Stage.OptionsPrompt:
                self.print_about_current_option()
                print(f"What is the prompt you want to go next to this UI element?")

            case self.Stage.OptionsValuesCombo:
                self.print_about_current_option()
                print(f"Add a selectable value to the ComboBox or press ENTER to stop adding values.")
                print(f"\tThis value is the text visible by the user in the GUI.")

            case self.Stage.OptionsDefaultValue:
                self.print_about_current_option()
                print(f"What do you want the default value of the UI element to be?")
                if type(self.currentOption) is jsonToQml.Options.ComboBox:
                    for i, elem in enumerate(self.currentOption.values):
                        print(f"{i + 1}. {elem["name"]}")

                if type(self.currentOption) is jsonToQml.Options.CheckBox:
                    print(f"For checked by default, type: \"true\", otherwise type \"false\"")

            case self.Stage.OptionsConfirm:
                self.print_about_current_option()
                print(f"Confirm you want to add this UI element. y/n")

            case self.Stage.OptionsAgain:
                self.print_already_added_options()
                print(f"Want to add another option? y/n")

            case self.Stage.Generate:
                print(f"Would you like to instantly generate the plugin? y/n")

            case self.Stage.GenerateAskFilePath:
                print(f"Where would you like to save this plugin? Enter a file path ending in .qml")

            case _:
                print("END")
                input()
                os.system('cls||clear')
                exit()

    def process_input(self, inp: str):
        match self.currentStage:
            case self.Stage.Start:
                self.currentStage = self.Stage.Name

            case self.Stage.Name:
                self.memory.name = inp[:20]
                self.currentStage = self.Stage.Version

            case self.Stage.Version:
                version = inp
                if inp == "":
                    version = "1.0"
                self.memory.version = version
                self.currentStage = self.Stage.ReadsScore

            case self.Stage.ReadsScore:
                if inp != 'y' and inp != 'n':
                    return
                readsScore = True
                if inp == 'n':
                    self.memory.readsScore = False
                self.memory.readsScore = readsScore
                self.currentStage = self.Stage.WritesScore

            case self.Stage.WritesScore:
                if inp != 'y' and inp != 'n':
                    return
                writesScore = True
                if inp == 'n':
                    self.memory.writesScore = False
                self.memory.writesScore = writesScore

                if self.memory.writesScore == True:
                    self.currentStage = self.Stage.SavePath
                else:
                    self.currentStage = self.Stage.ExecutablePath

            case self.Stage.SavePath:
                if inp == "":
                    inp = "./temp/temp"

                if not pathvalidate.is_valid_filepath(inp):
                    print(f"Not a valid file path, please try again. Press ENTER to proceed.")
                    input()
                    return
                
                self.memory.savePath = inp
                self.currentStage = self.Stage.ExecutablePath

            case self.Stage.ExecutablePath:
                if not pathvalidate.is_valid_filepath(inp):
                    print(f"Not a valid file path, please try again. Press ENTER to proceed.")
                    input()
                    return
                
                self.memory.executableScriptPath = inp
                self.currentStage = self.Stage.OptionsExplanation

            case self.Stage.OptionsExplanation:
                self.currentStage = self.Stage.OptionsType

            case self.Stage.OptionsType:
                try:
                    val = int(inp)
                except:
                    print(f"Not a valid number, please try again. Press ENTER to proceed.")
                    input()
                    return
                if val not in range(1, 6):
                    print(f"Not a valid number in the range, please try again. Press ENTER to proceed.")
                    input()
                    return
            
                obj = None
                match val:
                    case 1:
                        obj = jsonToQml.Options.TextField()
                    
                    case 2:
                        obj = jsonToQml.Options.CheckBox()
                    
                    case 3:
                        obj = jsonToQml.Options.ComboBox()

                    case 4:
                        obj = jsonToQml.Options.FileDialog()
                    
                    case 5:
                        self.currentStage = self.Stage.Generate
                        return
                
                self.currentOption = obj
                self.currentStage = self.Stage.OptionsCLA

            case self.Stage.OptionsCLA:
                self.currentOption.cla = inp
                self.currentStage = self.Stage.OptionsPrompt

            case self.Stage.OptionsPrompt:
                self.currentOption.prompt = inp
                if type(self.currentOption) == jsonToQml.Options.ComboBox:
                    self.currentStage = self.Stage.OptionsValuesCombo
                else:
                    self.currentStage = self.Stage.OptionsDefaultValue

            case self.Stage.OptionsValuesCombo:
                if inp == "":
                    self.currentStage = self.Stage.OptionsDefaultValue
                    return
                text = inp
                print(f"What value of the command-line argument should this correspond to?")
                print(f"\tThis value will be passed in the command-line call")
                print(f"\tEntering \"Name2\" here would make it so selecting {text} in the ComboBox passes \'{self.currentOption.cla} \"Name2\"\' to the command-line call")
                inp = input()
                d = dict()
                d["name"] = text
                d["arg"] = inp
                self.currentOption.values.append(d)

            case self.Stage.OptionsDefaultValue:
                if type(self.currentOption) is jsonToQml.Options.FileDialog:
                    if not pathvalidate.is_valid_filepath(inp):
                        print(f"Not a valid file path, please try again. Press ENTER to proceed.")
                        input()
                        return
                    self.currentOption.defaultValue = inp

                elif type(self.currentOption) is jsonToQml.Options.CheckBox:
                    if inp != "true" and inp != "false":
                        print(f"Not true or false, try again. Press ENTER to proceed.")
                        input()
                        return
                    self.currentOption.defaultValue = inp

                elif type(self.currentOption) is jsonToQml.Options.ComboBox:
                    try:
                        val = int(inp)
                    except:
                        print(f"Not a valid number, please try again. Press ENTER to proceed.")
                        input()
                        return
                    if val not in range(1, len(self.currentOption.values) + 1):
                        print(f"Not a valid number in the range, please try again. Press ENTER to proceed.")
                        input()
                        return
                    self.currentOption.defaultValue = self.currentOption.values[val-1]["name"]

                else:
                    self.currentOption.defaultValue = inp

                self.currentStage = self.Stage.OptionsConfirm

            case self.Stage.OptionsConfirm:
                if inp != 'y' and inp != 'n':
                    return
                if inp == 'y':
                    self.memory.options.append(self.currentOption)
                    
                self.currentOption = None
                self.currentStage = self.Stage.OptionsAgain

            case self.Stage.OptionsAgain:
                if inp != 'y' and inp != 'n':
                    return
                if inp == 'y':
                    self.currentOption = None
                    self.currentStage = self.Stage.OptionsType
                else:
                    self.currentStage = self.Stage.Generate

            case self.Stage.Generate:
                if inp != 'y' and inp != 'n':
                    return
                if inp == 'y':
                    self.currentStage = self.Stage.GenerateAskFilePath
                else:
                    self.currentStage = self.Stage.End

            case self.Stage.GenerateAskFilePath:
                if not pathvalidate.is_valid_filepath(inp):
                    print("Not a valid filepath, make sure it ends in .qml. Press ENTER to proceed.")
                    input()
                    return
                if os.path.splitext(inp)[1] != ".qml":
                    print("Not a valid filepath, make sure it ends in .qml. Press ENTER to proceed.")
                    input()
                    return
                
                first, ext = os.path.splitext(inp)
                jsonPath = first + '.json'
                self.memory.jsonify(jsonPath)
                jsonToQml.generate_qml_from_json(jsonPath, inp)
                print("Finished creating the JSON and QML. Press ENTER to proceed.")
                input()
                self.currentStage = self.Stage.End

    def run(self):
        while(True):
            if self.currentStage != self.Stage.Start:
                self.print_progress_bar()
            self.print_prompt()
            inp = input()
            self.process_input(inp)
            os.system('cls||clear')

class Remembrall:
    def __init__(self):
        self.name = ""
        self.version = ""
        self.readsScore = False
        self.writesScore = False
        self.savePath = ""
        self.executableScriptPath = ""
        self.options = []

    # TODO
    def jsonify(self, path: str):
        def convertOptionToDict(option):
            d = dict()
            typeString = ""
            match type(option):
                case jsonToQml.Options.TextField:
                    typeString = "textField"
                case jsonToQml.Options.CheckBox:
                    typeString = "checkBox"
                case jsonToQml.Options.ComboBox:
                    typeString = "comboBox"
                case jsonToQml.Options.FileDialog:
                    typeString = "fileDialog"
                case _:
                    raise Exception("Not a valid type when serializing option")
            d["type"] = typeString
            d["promptString"] = option.prompt
            d["defaultValue"] = option.defaultValue
            d["cla"] = option.cla
            if type(option) is jsonToQml.Options.ComboBox:
                d["values"] = option.values

            return d

        d = dict()
        d["pluginName"] = self.name
        d["pluginVersion"] = self.version
        d["readsScore"] = self.readsScore
        d["writesScore"] = self.writesScore
        d["defaultSavePath"] = self.savePath
        d["executableScriptPath"] = self.executableScriptPath
        d["optionFields"] = []
        for opt in self.options:
            d["optionFields"].append(convertOptionToDict(opt))

        with open(path, "w") as f:
            json.dump(d, f)

if __name__ == "__main__":
    wizard = Dumbledore()
    wizard.run()