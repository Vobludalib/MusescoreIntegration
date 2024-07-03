import json
import os
import sys
import jinja2

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
                if os.path.splitext(self.executableScriptPath)[1] == ".py":
                    self.isPython = True
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
        pluginVars = { "executableScriptPath": self.executableScriptPath, "defaultSavePath": self.defaultSavePath, "readsScore": self.readsScore, "writesScore": self.writesScore }
        outputText = pluginCoreText = template.render(pluginVars)
        return outputText

    def render_functions(self, jinjaenv):
        template = jinjaenv.get_template("functionsTemplate.jinja2")
        functionVars = { "writesScore": self.writesScore }
        outputText = template.render(functionVars)
        return outputText

    #TODO: Refactor for inheritance
    class TextField:
        def __init__(self, prompt: str = "", defaultValue: str = "", cla: str = ""):
            self.prompt = prompt
            self.defaultValue = defaultValue
            self.cla = cla

        def render(self, id: str, previousElemId: str, jinjaenv):
            template = jinjaenv.get_template("textFieldTemplate.jinja2")
            templateVars = {"id": id, "previousElemId": previousElemId, "defaultValue": self.defaultValue, "cla": self.cla, "prompt": self.prompt}
            outputText = template.render(templateVars)
            return outputText

    class FileDialog:
        def __init__(self, prompt: str = "", defaultValue: str = "", cla: str = ""):
            self.prompt = prompt
            self.defaultValue = defaultValue
            self.cla = cla

        def render(self, id: str, previousElemId: str, jinjaenv):
            template = jinjaenv.get_template("fileDialogTemplate.jinja2")
            templateVars = {"id": id, "previousElemId": previousElemId, "defaultValue": self.defaultValue, "cla": self.cla, "prompt": self.prompt}
            outputText = template.render(templateVars)
            return outputText

    class ComboBox:
        def __init__(self, prompt: str = "", values: list = [], defaultValue: str = "", cla: str = ""):
            self.prompt = prompt
            self.values = values
            self.defaultValue = defaultValue
            self.cla = cla

        def render(self, id: str, previousElemId: str, jinjaenv):
            template = jinjaenv.get_template("comboBoxTemplate.jinja2")
            defaultIndex = 0
            for i in range(len(self.values)):
                self.values[i]["text"] = self.values[i]["name"]
                if self.values[i]["name"] == self.defaultValue:
                    defaultIndex = i
            templateVars = {"id": id, "previousElemId": previousElemId, "defaultIndex": defaultIndex, "cla": self.cla, "prompt": self.prompt, "values": self.values}
            outputText = template.render(templateVars)
            return outputText

    class CheckBox:
        def __init__(self, prompt: str = "", defaultValue: str = "", cla: str = ""):
            self.prompt = prompt
            self.defaultValue = defaultValue
            self.cla = cla

        def render(self, id: str, previousElemId: str, jinjaenv):
            template = jinjaenv.get_template("checkBoxTemplate.jinja2")
            templateVars = {"id": id, "previousElemId": previousElemId, "defaultValue": self.defaultValue, "cla": self.cla, "prompt": self.prompt}
            outputText = template.render(templateVars)
            return outputText

def expected_usage_string() -> str:
    return "Expected usage:\n\tpython jsonToQml.py {path_to_config_json.json} {path_to_output_qml_file.qml}"

def generate_qml_from_json(inputPath: str, outputPath: str):
    options = Options()
    templateLoader = jinja2.FileSystemLoader( searchpath=os.path.join(".", "templates"))
    jinjaenv = jinja2.Environment(loader=templateLoader)
    options.parse_json(os.path.join(inputPath))
    flagsText = options.render_flags(jinjaenv)
    optionsText = options.render_all_options(jinjaenv)
    pluginCoreText = options.render_plugin_core(jinjaenv)
    functionsText = options.render_functions(jinjaenv)
    fullVars = {"pluginName": options.pluginName, "pluginVersion": options.pluginVersion, "requiresScore": options.readsScore, "flagsInitText": flagsText, "claOptionsText": optionsText, "pluginCoreText": pluginCoreText, "functionsText": functionsText}
    wholeText = jinjaenv.get_template("pluginTemplate.jinja2").render(fullVars)
    with open(outputPath, 'w') as f:
        f.write(wholeText)

if __name__ == "__main__":
    args = sys.argv
    if len(args) != 3:
        raise Exception(f"Expected amount of args: 2, got {len(args) - 1}\n{expected_usage_string()}")
    if os.path.splitext(args[2])[1] != ".qml": 
        raise Exception(f"Output file path is not .qml\n{expected_usage_string()}")
    if os.path.splitext(args[1])[1] != ".json":
        raise Exception(f"Input file path is not .json\n{expected_usage_string()}")
    
    inputPath = args[1]
    outputPath = args[2]

    generate_qml_from_json(inputPath, outputPath)    