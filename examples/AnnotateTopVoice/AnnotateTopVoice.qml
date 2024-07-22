import QtQuick 2.1
import QtQuick.Dialogs 1.2
import QtQuick.Controls 1.0
import MuseScore 3.0
import FileIO 3.0
import Qt.labs.folderlistmodel 2.2
import Qt.labs.platform 1.0

MuseScore {
	menuPath: "Plugins.AnnotateTopVoice"
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
    flags = {  "--everyOther": { toPrint: false, value: "" }, "--color": { toPrint: true, value: "Red" }}
    loadingText.visible = false;
    executableScript.source = getLocalPath(executableScript.source);
    mscTempFileStorePath.source = getLocalPath(mscTempFileStorePath.source);
}

CheckBox {
    id: option0
    text: qsTr("Only annotate every other note?")
    anchors.top: window.top
    anchors.left: window.left
    anchors.topMargin: 10
    anchors.leftMargin: 10
    anchors.bottomMargin: 10
    checked: false
    onClicked: {
        if (option0.checked) {
            flags["--everyOther"].toPrint = true;
        } else {
            flags["--everyOther"].toPrint = false;
        }
    }
}
ComboBox {
    id: option1
    currentIndex: 0
    width: 200
    anchors.top: option0.bottom
    anchors.left: window.left
    anchors.topMargin: 10
    anchors.leftMargin: 10
    anchors.bottomMargin: 10
    model: ListModel {
        id: option1Model
        ListElement { text: "Red"; value: "red" }
        ListElement { text: "Blue"; value: "blue" }
        ListElement { text: "Green"; value: "green" }
    }
    onCurrentIndexChanged: {
        var val = option1Model.get(currentIndex).value;
        changeoption1Value(val);
    }
}

Text {
    id: option1Prompt
    text: qsTr("Choose a color:")
    anchors.left: option1.right
    anchors.top: option1.top
    anchors.bottom: option1.bottom
    anchors.leftMargin: 10
}

function changeoption1Value(val) {
    flags["--color"].value = val;
}

FileIO {
    id: executableScript
    source: "./AnnotateTopVoice.py"
    onError: console.log(msg)
}

FileIO {
    id: mscTempFileStorePath
    source: "./temp/temp"
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
    
    var tempFilePath = mscTempFileStorePath.source;
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

}