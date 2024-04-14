import QtQuick 2.9
import QtQuick.Dialogs 1.0
import QtQuick.Controls 1.0
import MuseScore 3.0
import FileIO 3.0

MuseScore {
	menuPath: "Plugins.PythonServerInterop"
	version: "0.1"
	id:window
	width: 800; height: 500;
	requiresScore: false
	pluginType: "dialog"

	onRun: {}

	FileIO {
		id: mscTempXmlFile
		source: tempPath() + "/mscTempXmlFile.xml"
		onError: console.log(msg)
	}

	Button {
		id: buttonSave
		text: qsTr("Send to Python server")
		anchors.left: window.left

		onClicked: {
			writeScore(curScore, mscTempXmlFile.source, "xml");
			var content = "hello";
			var urlToServer = "http://127.0.0.1:" + serverPort();
			var requestValue = "/plugin";
			var sendUrl = urlToServer + requestValue;

			console.log(sendUrl);
			var request = new XMLHttpRequest();
			request.open("POST", sendUrl, false);
                        console.log("Request opened");
			request.setRequestHeader("Content-Type", "text/plain")
			request.setRequestHeader("Content-length", content.length);
                        request.send(content);
                        console.log("Request sent");
                        console.log(request.readyState);
                        console.log(request.responseText);
                        
		}
	}


	function serverPort()
	{
		return "5000";
	}
}