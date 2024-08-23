import QtQuick 2.1
import QtQuick.Dialogs 1.2
import QtQuick.Controls 1.0
import MuseScore 3.0
import FileIO 3.0
import Qt.labs.folderlistmodel 2.2
import Qt.labs.platform 1.0

MuseScore {
	menuPath: "Plugins.Delasol"
	version: "0.1"
	id: window
	width: 800; height: 500;
	requiresScore: true
	pluginType: "dialog"

	QProcess {
		id: proc
	}

property var flags: {}

onRun: {
    flags = {  "--style": { toPrint: true, value: "continental" }, "--showWeights": { toPrint: false, value: "" }, "--showNonBest": { toPrint: false, value: "" }}
    loadingText.visible = false;
    executableScript.source = getLocalPath(executableScript.source);
    mscTempFileStorePath.source = getLocalPath(mscTempFileStorePath.source);
}

ComboBox {
    id: option0
    currentIndex: 0
    width: 200
    anchors.top: window.top
    anchors.left: window.left
    anchors.topMargin: 10
    anchors.leftMargin: 10
    anchors.bottomMargin: 10
    model: ListModel {
        id: option0Model
        ListElement { text: "Continental"; value: "continental" }
        ListElement { text: "English"; value: "english" }
    }
    onCurrentIndexChanged: {
        var val = option0Model.get(currentIndex).value;
        changeoption0Value(val);
    }
}

Text {
    id: option0Prompt
    text: qsTr("What style of solmization?")
    anchors.left: option0.right
    anchors.top: option0.top
    anchors.bottom: option0.bottom
    anchors.leftMargin: 10
}

function changeoption0Value(val) {
    flags["--style"].value = val;
}
CheckBox {
    id: option1
    text: qsTr("Show estimation weights?")
    anchors.top: option0.bottom
    anchors.left: window.left
    anchors.topMargin: 10
    anchors.leftMargin: 10
    anchors.bottomMargin: 10
    checked: false
    onClicked: {
        if (option1.checked) {
            flags["--showWeights"].toPrint = true;
        } else {
            flags["--showWeights"].toPrint = false;
        }
    }
}
CheckBox {
    id: option2
    text: qsTr("Show more estimates?")
    anchors.top: option1.bottom
    anchors.left: window.left
    anchors.topMargin: 10
    anchors.leftMargin: 10
    anchors.bottomMargin: 10
    checked: false
    onClicked: {
        if (option2.checked) {
            flags["--showNonBest"].toPrint = true;
        } else {
            flags["--showNonBest"].toPrint = false;
        }
    }
}

FileIO {
    id: executableScript
    source: "./wrapper.py"
    onError: console.log(msg)
}

FileIO {
    id: mscTempFileStorePath
    source: "./temp/"
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
                loadingText.visible = true;
		var call = createCLICallFromFlags();
		proc.start(call);
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
    
    var tempFilePath = mscTempFileStorePath.source + getCurrentTimeString();
    writeScore(curScore, tempFilePath, "mxl");
    call = call + ' --tempPath "' + tempFilePath + '.mxl"';
    
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