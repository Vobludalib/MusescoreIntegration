import QtQuick 2.1
import QtQuick.Dialogs 1.2
import QtQuick.Controls 1.0
import MuseScore 3.0
import FileIO 3.0
import Qt.labs.folderlistmodel 2.2
import Qt.labs.platform 1.0

MuseScore {
	menuPath: "Plugins.LaunchStuff"
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
    flags = {  "--check": { toPrint: true, value: "" }}
    loadingText.visible = false;
    executableScript.source = getLocalPath(executableScript.source);
    mscTempFileStorePath.source = getLocalPath(mscTempFileStorePath.source);
}

CheckBox {
    id: option0
    text: qsTr("Enable weird feature?")
    anchors.top: window.top
    anchors.left: window.left
    anchors.topMargin: 10
    anchors.leftMargin: 10
    anchors.bottomMargin: 10
    checked: true
    onClicked: {
        if (option0.checked) {
            flags["--check"].toPrint = true;
        } else {
            flags["--check"].toPrint = false;
        }
    }
}

FileIO {
    id: executableScript
    source: "./test.py"
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