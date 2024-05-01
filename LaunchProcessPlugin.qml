import QtQuick 2.1
import QtQuick.Dialogs 1.2
import QtQuick.Controls 1.0
import MuseScore 3.0
import FileIO 3.0
import Qt.labs.folderlistmodel 2.2
import Qt.labs.platform 1.0


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

	Text {
		id: executablePath
		text: qsTr(executableScript.source)
		anchors.bottom: chooseExecutableButton.top
		anchors.left: chooseExecutableButton.left
		anchors.topMargin: 10
		anchors.bottomMargin: 10
		anchors.leftMargin: 10
	}

	FileDialog {
		id: openDialog
		title: qsTr("Please choose an executable file")
		folder: shortcuts.home
		onAccepted: {
			console.log("You chose: " + openDialog.file)
			executableScript.source = getLocalPath(String(openDialog.file));
			executablePath.text = executableScript.source;
		}
		onRejected: {
			console.log("Canceled")
		}
	}
	
	Button {
		id: chooseExecutableButton
		text: qsTr("Choose executable")
		anchors.bottom: window.bottom
		anchors.left: window.left
		anchors.topMargin: 10
		anchors.bottomMargin: 10
		anchors.leftMargin: 10
		width: 130
		height: 20
		onClicked: {
			openDialog.open();
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

	// TextField {
	// 	id: tempFolderSelectorTextField
	// 	anchors.right: debugOptions.right
	// 	placeholderText: qsTr(mscTempXmlFolder.source + mscTempXmlFile.source)
	// 	width: 250
	// 	height: 50
	// 	onAccepted: {
	// 		var folder = text;
	// 		console.log("You chose: " + folder)
	// 		if (folder)
	// 		{
	// 			mscTempXmlFolder.source = folder;
	// 		}
	// 	}
	// }

	FolderDialog {
		id: tempFolderDialog
		title: qsTr("Please choose a temp folder")
		folder: shortcuts.home
		onAccepted: {
			console.log("You chose: " + tempFolderDialog.folder)
			mscTempXmlFolder.source = getLocalPath(String(tempFolderDialog.folder));
			tempFolder.text = mscTempXmlFolder.source;
		}
		onRejected: {
			console.log("Canceled")
		}
	}

	Text {
		id: tempFolder
		text: qsTr(mscTempXmlFolder.source)
		anchors.top: tempFolderButton.bottom
		anchors.right: tempFolderButton.right
		anchors.topMargin: 10
	}

	
	Button {
		id: tempFolderButton
		text: qsTr("Choose temp folder")
		anchors.right: debugOptions.right
		width: 130
		height: 20
		onClicked: {
			// tempFolderDialog.selectFolder = true;
			tempFolderDialog.open();
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

	// Taken from abc_ImpEx
    function getLocalPath(path) { // Remove "file://" from paths and third "/" from  paths in Windows
        path = path.replace(/^(file:\/{2})/,"");
        if (Qt.platform.os == "windows") { 
			path = path.replace(/^\//,"");
			path = path.replace(/\//g, "\\");
		}
		path = decodeURIComponent(path);            
        return path;
    }

}