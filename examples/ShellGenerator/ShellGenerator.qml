import QtQuick 2.1
import QtQuick.Dialogs 1.2
import QtQuick.Controls 1.0
import MuseScore 3.0
import FileIO 3.0
import Qt.labs.folderlistmodel 2.2
import Qt.labs.platform 1.0

MuseScore {
	menuPath: "Plugins.ShellGeneratorFromJs"
	version: "1.0"
	id: window
	width: 800; height: 500;
	requiresScore: false
	pluginType: "dialog"

	QProcess {
		id: proc
	}

property var flags: {}

onRun: {
    flags = {  "--path": { toPrint: true, value: getLocalPath("C:\Users\simon\OneDrive\Documents\MuseScore3\Plugins\ShellGenerator\values.json") }}
    loadingText.visible = false;
    executableScript.source = getLocalPath(executableScript.source);
    mscTempFileStorePath.source = getLocalPath(mscTempFileStorePath.source);
}

FileDialog {
    id: option0Dialog
    title: qsTr("Please choose a file")
    onAccepted: {
        var val = getLocalPath(String(option0Dialog.file));
        console.log("You chose: " + val)
        updateoption0Flags(val);
        option0Text.text = val;
    }
    onRejected: {
        console.log("Canceled")
    }
}

Button {
    id: option0
    text: qsTr("Choose the JSON file:")
    anchors.top: window.top
    anchors.left: window.left
    anchors.topMargin: 10
    anchors.leftMargin: 10
    anchors.bottomMargin: 10
    onClicked: {
        option0Dialog.open();
    }
}

Text {
    id: option0Text
    text: qsTr(getLocalPath("C:/Users/simon/OneDrive/Documents/MuseScore3/Plugins/ShellGenerator/values.json"))
    anchors.left: option0.right
    anchors.top: option0.top
    anchors.bottom: option0.bottom
    anchors.leftMargin: 10
}

function updateoption0Flags(path) { // fields cannot be changed inside OnAccepted handler
      flags["--path"].value = path;
}

FileIO {
    id: executableScript
    source: "./GenerateShellFromJson.py"
    onError: console.log(msg)
}

FileIO {
    id: mscTempFileStorePath
    source: ""
}

Text {
	id: loadingText
	text: qsTr("LOADING!!!")
	anchors.centerIn: window
}

Button {
	id: buttonSave
	text: qsTr("Launch executable")
	anchors.bottom: window.bottom
	anchors.left: window.left
	anchors.topMargin: 10
	anchors.bottomMargin: 10
	anchors.leftMargin: 10

	onClicked: {
		var call = createCLICallFromFlags();
		console.log(call);
		proc.start(call);
		loadingText.visible = true;
		var val = proc.waitForFinished(10000);
		loadingText.visible = false;
		var output = proc.readAllStandardOutput();
		console.log("Finished python script with output: " + output);
		
		var correctOutputPath = getLocalPath(String(output));
		console.log('"' + correctOutputPath + '"');
		readScore(correctOutputPath);
		
	}
}

function createCLICallFromFlags() {
    var call = "python";
    call = call + ' "' + executableScript.source + '"';
    
    for (var key in flags) {
        if (flags[key].toPrint) {
            call = call + " " + key;
            if (flags[key].value != "") {
                call = call + ' "' + flags[key].value + '"';
            }
        }
    }
    return call;
}

function getLocalPath(path) { // Remove "file://" from paths and third "/" from  paths in Windows
    path = path.trim();
    path = path.replace(/^(file:\/{2})/,"");

    var pluginsFolder = window.filePath;
    path = path.replace(/^\./, pluginsFolder);

    if (Qt.platform.os == "windows") { 
        path = path.replace(/^\//,"");
        path = path.replace(/\//g, "\\");
    }
    path = decodeURIComponent(path);            
    return path;
}

function getCurrentTimeString() {
    var cT = new Date();
    var timeString = cT.toLocaleDateString(Qt.locale("en_CA"), Locale.ShortFormat);
    timeString = timeString + "-" + cT.getHours() + "-" + cT.getMinutes() + "-" + cT.getSeconds();
    return timeString;
}

}