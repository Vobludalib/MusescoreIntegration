import json
import os
import jinja2

"""
TODO:

- Update github documentation
    - Default save path is given in JSON
    - No default read path, as that is returned as stdout by the process
- Refactor code to handle the above explicitly DONE
- Require score functionality DONE
- No load/write also options DONE
- Wizard
- CLargs for this py script to be output qml file name DOCUMENT behaviour
"""

class Options:
    def __init__(self):
        self.pluginName = ""
        self.pluginVersion = ""
        self.readsScore = False
        self.writesScore = False
        self.defaultSavePath = ""
        self.executableScriptPath = ""
        self.options = []

    def parse_json(self, file: str):
        with open(file, "r") as f:
            data = json.load(f)
            if data.get("pluginName") is not None:
                self.pluginName = data["pluginName"]
            if data.get("pluginVersion") is not None:
                self.pluginVersion = data["pluginVersion"]
            if data.get("readsScore") is True:
                self.readsScore = True
            if data.get("writesScore") is True:
                self.writesScore = True
            if data.get("defaultSavePath") is not None:
                self.defaultSavePath = data["defaultSavePath"]
            if data.get("executableScriptPath") is not None:
                self.executableScriptPath = data["executableScriptPath"]
            if data.get("optionFields") is not None:
                for object in data["optionFields"]:
                    match object["type"]:
                        case "textField":
                            prompt = object.get("promptString", "")
                            defaultValue = object.get("defaultValue", "")
                            cla = object.get("cla", "")
                            self.options.append(self.TextField(prompt, defaultValue, cla))
                        case "fileDialog":
                            prompt = object.get("promptString", "")
                            defaultValue = object.get("defaultValue", "")
                            cla = object.get("cla", "")
                            self.options.append(self.FileDialog(prompt, defaultValue, cla))
                        case "comboBox":
                            prompt = object.get("promptString", "")
                            values = object.get("values", [])
                            defaultValue = object.get("defaultValue", "")
                            cla = object.get("cla", "")
                            self.options.append(self.ComboBox(prompt, values, defaultValue, cla))
                        case "checkBox":
                            prompt = object.get("promptString", "")
                            defaultValue = object.get("defaultValue", False)
                            cla = object.get("cla", "")
                            self.options.append(self.CheckBox(prompt, defaultValue, cla))

    def render_flags(self, jinjaenv):
        template = jinjaenv.get_template("flagsTemplate.jinja2")
        templateVars = {"flags": self.prepare_flags()}
        outputText = template.render(templateVars)
        return outputText

    def prepare_flags(self):
        class Flag:
            def __init__(self, name: str, toPrint: bool, value: str):
                self.name = name
                self.toPrint = toPrint
                self.value = value

        flags = []

        for option in self.options:
            if isinstance(option, self.CheckBox):
                flags.append(Flag(option.cla, "true" if option.defaultValue is True else "false", '""'))
            elif isinstance(option, self.FileDialog):
                flags.append(Flag(option.cla, "true", 'getLocalPath("' + option.defaultValue + '")'))
            else:
                flags.append(Flag(option.cla, "true", '"' + option.defaultValue + '"'))

        return flags

    def render_all_options(self, jinjaenv):
        texts = []
        for i in range(len(self.options)):
            val = self.options[i].render("option" + str(i), "window" if i == 0 else "option" + str(i - 1), jinjaenv)
            texts.append(val)

        return "\n".join(texts)

    def render_plugin_core(self, jinjaenv):
        template = jinjaenv.get_template("pluginCoreTemplate.jinja2")
        pluginVars = { "executableScriptPath": options.executableScriptPath, "defaultSavePath": options.defaultSavePath, "readsScore": options.readsScore, "writesScore": options.writesScore }
        outputText = pluginCoreText = template.render(pluginVars)
        return outputText

    def render_functions(self, jinjaenv):
        template = jinjaenv.get_template("functionsTemplate.jinja2")
        functionVars = { "writesScore": options.writesScore }
        outputText = template.render(functionVars)
        return outputText

    class TextField:
        def __init__(self, prompt: str, defaultValue: str, cla: str):
            self.prompt = prompt
            self.defaultValue = defaultValue
            self.cla = cla

        def render(self, id: str, previousElemId: str, jinjaenv):
            template = jinjaenv.get_template("textFieldTemplate.jinja2")
            templateVars = {"id": id, "previousElemId": previousElemId, "defaultValue": self.defaultValue, "cla": self.cla, "prompt": self.prompt}
            outputText = template.render(templateVars)
            return outputText

    class FileDialog:
        def __init__(self, prompt: str, defaultValue: str, cla: str):
            self.prompt = prompt
            self.defaultValue = defaultValue
            self.cla = cla

        def render(self, id: str, previousElemId: str, jinjaenv):
            template = jinjaenv.get_template("fileDialogTemplate.jinja2")
            templateVars = {"id": id, "previousElemId": previousElemId, "defaultValue": self.defaultValue, "cla": self.cla, "prompt": self.prompt}
            outputText = template.render(templateVars)
            return outputText

    class ComboBox:
        def __init__(self, prompt: str, values: list, defaultValue: str, cla: str):
            self.prompt = prompt
            self.values = values
            self.defaultValue = defaultValue
            self.cla = cla

        def render(self, id: str, previousElemId: str, jinjaenv):
            template = jinjaenv.get_template("comboBoxTemplate.jinja2")
            defaultIndex = 0
            for i in range(len(self.values)):
                if self.values[i]["text"] == self.defaultValue:
                    defaultIndex = i
                    break
            templateVars = {"id": id, "previousElemId": previousElemId, "defaultIndex": defaultIndex, "cla": self.cla, "prompt": self.prompt, "values": self.values}
            outputText = template.render(templateVars)
            return outputText

    class CheckBox:
        def __init__(self, prompt: str, defaultValue: bool, cla: str):
            self.prompt = prompt
            self.defaultValue = defaultValue
            self.cla = cla

        def render(self, id: str, previousElemId: str, jinjaenv):
            template = jinjaenv.get_template("checkBoxTemplate.jinja2")
            templateVars = {"id": id, "previousElemId": previousElemId, "defaultValue": self.defaultValue, "cla": self.cla, "prompt": self.prompt}
            outputText = template.render(templateVars)
            return outputText

if __name__ == "__main__":
    options = Options()
    templateLoader = jinja2.FileSystemLoader( searchpath=os.path.join(".", "templates"))
    jinjaenv = jinja2.Environment(loader=templateLoader)
    options.parse_json(os.path.join(".", "example.json"))
    flagsText = options.render_flags(jinjaenv)
    optionsText = options.render_all_options(jinjaenv)
    pluginCoreText = options.render_plugin_core(jinjaenv)
    functionsText = options.render_functions(jinjaenv)
    fullVars = {"pluginName": options.pluginName, "pluginVersion": options.pluginVersion, "requiresScore": options.readsScore, "flagsInitText": flagsText, "claOptionsText": optionsText, "pluginCoreText": pluginCoreText, "functionsText": functionsText}
    wholeText = jinjaenv.get_template("pluginTemplate.jinja2").render(fullVars)
    with open("out.qml", 'w') as f:
        f.write(wholeText)