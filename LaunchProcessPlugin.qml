import QtQuick 2.9
import QtQuick.Dialogs 1.0
import Qt.labs.platform 1.0
import QtQuick.Controls 1.0
import MuseScore 3.0
import FileIO 3.0

MuseScore {
	menuPath: "Plugins.LaunchProcess"
	version: "0.1"
	id:window
	width: 800; height: 500;
	requiresScore: true
	pluginType: "dialog"

	QProcess {
		id: proc
	}

	// TODO:
	// onRun could search what specific Python version to call with + install location of script given a name to look for
	// Inspiration can be taken from abc_ImpEx.qml
	// Config files for storing where script + temp folder is
	// Get readAllStandardOutput working, so script can output return file path
	// Get Linux up and running as dual boot - handling + testing different formats of file paths ('/' vs '\')
	// Test on other MacOs computer (or after update) to see compat. issues with MacOs

	onRun: {
		debugOptions.visible = false;
		everyOtherColour.checked = true;
		loadingText.visible = false;
	}

	FileIO {
		id: executableScript
		source: "C:\\Users\\simon\\OneDrive\\Desktop\\CodingProjects\\MusescoreIntegration\\Music21Exploration\\AnnotateTopVoice.py"
		onError: console.log(msg)
	}

	FileIO {
		id: mscTempXmlFile
		source: "\\mscTempXmlFile.xml"
	}

	FileIO {
		id: mscTempXmlFolder
		source: "C:\\Users\\simon\\OneDrive\\Desktop\\CodingProjects\\MusescoreIntegration\\temp"
		onError: console.log(msg)
	}

	TextField {
		id: chooseExecutableButton
		placeholderText: qsTr(executableScript.source)
		anchors.bottom: window.bottom
		anchors.left: window.left
		anchors.topMargin: 10
		anchors.bottomMargin: 10
		anchors.leftMargin: 10
		width: 300
		height: 50
		onAccepted: {
			var path = text;
			if (path)
			{
				executableScript.source = path;
			}
		}
	}

	Button {
		id: debugButton
		text: qsTr("Debug options")
		anchors.bottom: window.bottom
		anchors.right: window.right
		anchors.topMargin: 10
		anchors.rightMargin: 10
		anchors.leftMargin: 10
		anchors.bottomMargin: 10
		onClicked: {
			if (debugOptions.visible)
			{
				debugOptions.visible = false;
			} else {
			debugOptions.visible = true;
		}
	}
}

Item {
	id: processOptions
	anchors.top: window.top
	anchors.left: window.left
	anchors.topMargin: 10
	anchors.leftMargin: 10

	CheckBox {
		id: everyOtherColour
		text: qsTr("Colouring every note")
		onClicked: {
			if (everyOtherColour.text == "Colouring every other note")
			{
				everyOtherColour.text = "Colouring every note";
			} else {
			everyOtherColour.text = "Colouring every other note";
		}
	}
}

Button {
	id: colorPickerButton
	text: qsTr("Choose colour: ")
	anchors.top: everyOtherColour.bottom
	anchors.topMargin: 20
	onClicked: {
		colorPicker.open();
	}
}

Rectangle {
	width: 20
	height: width
	color: colorPicker.color
	border.width: 2
	border.color: "black"
	radius: width*0.5
	anchors.left: colorPickerButton.right
	anchors.top: colorPickerButton.top
	anchors.leftMargin: 10
}

ColorDialog {
	id: colorPicker
}
}

Item {
	id: debugOptions
	anchors.top: window.top
	anchors.right: window.right
	anchors.topMargin: 10
	anchors.rightMargin: 10

	TextField {
		id: tempFolderSelectorTextField
		anchors.right: debugOptions.right
		placeholderText: qsTr(mscTempXmlFolder.source + mscTempXmlFile.source)
		width: 250
		height: 50
		onAccepted: {
			var folder = text;
			console.log("You chose: " + folder)
			if (folder)
			{
				mscTempXmlFolder.source = folder;
			}
		}
	}
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
	anchors.left: chooseExecutableButton.right
	anchors.topMargin: 10
	anchors.bottomMargin: 10
	anchors.leftMargin: 10

	onClicked: {
		print(executableScript.source);
		var launchString = 'python "' + executableScript.source + '"';
		var tempFilePath = mscTempXmlFolder.source + mscTempXmlFile.source;
		writeScore(curScore, tempFilePath, "xml");
		var launchString = launchString + ' -tempPath "' + tempFilePath + '"';
		if (everyOtherColour.checked)
		{
			var launchString = launchString + ' --everyOther';
		}
		var launchString = launchString + ' -c "' + colorPicker.color + '"';
		console.log(launchString);
		proc.start(launchString);
		loadingText.visible = true;
		var val = proc.waitForFinished(10000);
		loadingText.visible = false;
		var output = proc.readAllStandardOutput();
		console.log("Finished python script");
		console.log(output);
		readScore("C:\\Users\\simon\\OneDrive\\Desktop\\CodingProjects\\MusescoreIntegration\\temp\\tempColoured.mxl");
	}
}
}