/**
 *  Catroid: An on-device visual programming system for Android devices
 *  Copyright (C) 2010-2013 The Catrobat Team
 *  (<http://developer.catrobat.org/credits>)
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU Affero General Public License as
 *  published by the Free Software Foundation, either version 3 of the
 *  License, or (at your option) any later version.
 *
 *  An additional term exception under section 7 of the GNU Affero
 *  General Public License, version 3, is available at
 *  http://developer.catrobat.org/license_additional_term
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 *  GNU Affero General Public License for more details.
 *
 *  You should have received a copy of the GNU Affero General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
package org.catrobat.catroid.io;

import static org.catrobat.catroid.common.Constants.BACKPACK_DIRECTORY;
import static org.catrobat.catroid.common.Constants.BACKPACK_IMAGE_DIRECTORY;
import static org.catrobat.catroid.common.Constants.BACKPACK_SOUND_DIRECTORY;
import static org.catrobat.catroid.common.Constants.DEFAULT_ROOT;
import static org.catrobat.catroid.common.Constants.IMAGE_DIRECTORY;
import static org.catrobat.catroid.common.Constants.NO_MEDIA_FILE;
import static org.catrobat.catroid.common.Constants.PROJECTCODE_NAME;
import static org.catrobat.catroid.common.Constants.SOUND_DIRECTORY;
import static org.catrobat.catroid.utils.Utils.buildPath;
import static org.catrobat.catroid.utils.Utils.buildProjectPath;

import com.thoughtworks.xstream.XStream;
import com.thoughtworks.xstream.converters.reflection.FieldDictionary;
import com.thoughtworks.xstream.converters.reflection.PureJavaReflectionProvider;

import org.catrobat.catroid.ProjectManager;
import org.catrobat.catroid.common.Constants;
import org.catrobat.catroid.common.FileChecksumContainer;
import org.catrobat.catroid.common.LookData;
import org.catrobat.catroid.common.ProjectData;
import org.catrobat.catroid.common.SoundInfo;
import org.catrobat.catroid.content.BroadcastScript;
import org.catrobat.catroid.content.Project;
import org.catrobat.catroid.content.Script;
import org.catrobat.catroid.content.Sprite;
import org.catrobat.catroid.content.StartScript;
import org.catrobat.catroid.content.WhenScript;
import org.catrobat.catroid.content.XmlHeader;
import org.catrobat.catroid.content.bricks.BrickBaseType;
import org.catrobat.catroid.content.bricks.BroadcastBrick;
import org.catrobat.catroid.content.bricks.BroadcastReceiverBrick;
import org.catrobat.catroid.content.bricks.BroadcastWaitBrick;
import org.catrobat.catroid.content.bricks.ChangeBrightnessByNBrick;
import org.catrobat.catroid.content.bricks.ChangeGhostEffectByNBrick;
import org.catrobat.catroid.content.bricks.ChangeSizeByNBrick;
import org.catrobat.catroid.content.bricks.ChangeVariableBrick;
import org.catrobat.catroid.content.bricks.ChangeVolumeByNBrick;
import org.catrobat.catroid.content.bricks.ChangeXByNBrick;
import org.catrobat.catroid.content.bricks.ChangeYByNBrick;
import org.catrobat.catroid.content.bricks.ClearGraphicEffectBrick;
import org.catrobat.catroid.content.bricks.ComeToFrontBrick;
import org.catrobat.catroid.content.bricks.DroneFlipBrick;
import org.catrobat.catroid.content.bricks.DroneLandBrick;
import org.catrobat.catroid.content.bricks.DroneMoveBackwardBrick;
import org.catrobat.catroid.content.bricks.DroneMoveDownBrick;
import org.catrobat.catroid.content.bricks.DroneMoveForwardBrick;
import org.catrobat.catroid.content.bricks.DroneMoveLeftBrick;
import org.catrobat.catroid.content.bricks.DroneMoveRightBrick;
import org.catrobat.catroid.content.bricks.DroneMoveUpBrick;
import org.catrobat.catroid.content.bricks.DronePlayLedAnimationBrick;
import org.catrobat.catroid.content.bricks.DroneTakeOffBrick;
import org.catrobat.catroid.content.bricks.ForeverBrick;
import org.catrobat.catroid.content.bricks.GlideToBrick;
import org.catrobat.catroid.content.bricks.GoNStepsBackBrick;
import org.catrobat.catroid.content.bricks.HideBrick;
import org.catrobat.catroid.content.bricks.IfLogicBeginBrick;
import org.catrobat.catroid.content.bricks.IfLogicElseBrick;
import org.catrobat.catroid.content.bricks.IfLogicEndBrick;
import org.catrobat.catroid.content.bricks.IfOnEdgeBounceBrick;
import org.catrobat.catroid.content.bricks.LegoNxtMotorActionBrick;
import org.catrobat.catroid.content.bricks.LegoNxtMotorStopBrick;
import org.catrobat.catroid.content.bricks.LegoNxtMotorTurnAngleBrick;
import org.catrobat.catroid.content.bricks.LegoNxtPlayToneBrick;
import org.catrobat.catroid.content.bricks.LoopBeginBrick;
import org.catrobat.catroid.content.bricks.LoopEndBrick;
import org.catrobat.catroid.content.bricks.LoopEndlessBrick;
import org.catrobat.catroid.content.bricks.MoveNStepsBrick;
import org.catrobat.catroid.content.bricks.NextLookBrick;
import org.catrobat.catroid.content.bricks.NoteBrick;
import org.catrobat.catroid.content.bricks.PlaceAtBrick;
import org.catrobat.catroid.content.bricks.PlaySoundBrick;
import org.catrobat.catroid.content.bricks.PointInDirectionBrick;
import org.catrobat.catroid.content.bricks.PointToBrick;
import org.catrobat.catroid.content.bricks.RepeatBrick;
import org.catrobat.catroid.content.bricks.SetBrightnessBrick;
import org.catrobat.catroid.content.bricks.SetGhostEffectBrick;
import org.catrobat.catroid.content.bricks.SetLookBrick;
import org.catrobat.catroid.content.bricks.SetSizeToBrick;
import org.catrobat.catroid.content.bricks.SetVariableBrick;
import org.catrobat.catroid.content.bricks.SetVolumeToBrick;
import org.catrobat.catroid.content.bricks.SetXBrick;
import org.catrobat.catroid.content.bricks.SetYBrick;
import org.catrobat.catroid.content.bricks.ShowBrick;
import org.catrobat.catroid.content.bricks.SpeakBrick;
import org.catrobat.catroid.content.bricks.StopAllSoundsBrick;
import org.catrobat.catroid.content.bricks.TurnLeftBrick;
import org.catrobat.catroid.content.bricks.TurnRightBrick;
import org.catrobat.catroid.content.bricks.WaitBrick;
import org.catrobat.catroid.content.bricks.WhenBrick;
import org.catrobat.catroid.content.bricks.WhenStartedBrick;
import org.catrobat.catroid.formulaeditor.UserVariable;
import org.catrobat.catroid.formulaeditor.UserVariablesContainer;
import org.catrobat.catroid.utils.ImageEditing;
import org.catrobat.catroid.utils.UtilFile;
import org.catrobat.catroid.utils.Utils;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public final class StorageHandler {
	private static final StorageHandler INSTANCE;
	private static final String TAG = StorageHandler.class.getSimpleName();
	private static final String XML_HEADER = "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\" ?>\n";
	private static final int JPG_COMPRESSION_SETTING = 95;

	private XStream xstream;

	private File backPackSoundDirectory;
	private FileInputStream fileInputStream;

	private Lock loadSaveLock = new ReentrantLock();

	// TODO: Since the StorageHandler constructor throws an exception, the member INSTANCE couldn't be assigned
	// directly and therefore we need this static block. Should be refactored and removed in the future.
	static {
		try {
			INSTANCE = new StorageHandler();
		} catch (IOException ioException) {
			throw new RuntimeException("Initialize StorageHandler failed");
		}
	}

	private StorageHandler() throws IOException {
		xstream = new XStream(new PureJavaReflectionProvider(new FieldDictionary(new CatroidFieldKeySorter())));
		xstream.processAnnotations(Project.class);
		xstream.processAnnotations(XmlHeader.class);
		xstream.processAnnotations(UserVariablesContainer.class);
		setXstreamAliases();

		if (!Utils.externalStorageAvailable()) {
			throw new IOException("Could not read external storage");
		}
		createCatroidRoot();
	}

	private void setXstreamAliases() {
		xstream.alias("look", LookData.class);
		xstream.alias("sound", SoundInfo.class);
		xstream.alias("userVariable", UserVariable.class);

		xstream.alias("broadcastScript", BroadcastScript.class);
		xstream.alias("script", Script.class);
		xstream.alias("object", Sprite.class);
		xstream.alias("startScript", StartScript.class);
		xstream.alias("whenScript", WhenScript.class);

		xstream.aliasField("object", BrickBaseType.class, "sprite");

		xstream.alias("broadcastBrick", BroadcastBrick.class);
		xstream.alias("broadcastReceiverBrick", BroadcastReceiverBrick.class);
		xstream.alias("broadcastWaitBrick", BroadcastWaitBrick.class);
		xstream.alias("changeBrightnessByNBrick", ChangeBrightnessByNBrick.class);
		xstream.alias("changeGhostEffectByNBrick", ChangeGhostEffectByNBrick.class);
		xstream.alias("changeSizeByNBrick", ChangeSizeByNBrick.class);
		xstream.alias("changeVariableBrick", ChangeVariableBrick.class);
		xstream.alias("changeVolumeByNBrick", ChangeVolumeByNBrick.class);
		xstream.alias("changeXByNBrick", ChangeXByNBrick.class);
		xstream.alias("changeYByNBrick", ChangeYByNBrick.class);
		xstream.alias("clearGraphicEffectBrick", ClearGraphicEffectBrick.class);
		xstream.alias("comeToFrontBrick", ComeToFrontBrick.class);
		xstream.alias("foreverBrick", ForeverBrick.class);
		xstream.alias("glideToBrick", GlideToBrick.class);
		xstream.alias("goNStepsBackBrick", GoNStepsBackBrick.class);
		xstream.alias("hideBrick", HideBrick.class);
		xstream.alias("ifLogicBeginBrick", IfLogicBeginBrick.class);
		xstream.alias("ifLogicElseBrick", IfLogicElseBrick.class);
		xstream.alias("ifLogicEndBrick", IfLogicEndBrick.class);
		xstream.alias("ifOnEdgeBounceBrick", IfOnEdgeBounceBrick.class);
		xstream.alias("legoNxtMotorActionBrick", LegoNxtMotorActionBrick.class);
		xstream.alias("legoNxtMotorStopBrick", LegoNxtMotorStopBrick.class);
		xstream.alias("legoNxtMotorTurnAngleBrick", LegoNxtMotorTurnAngleBrick.class);
		xstream.alias("legoNxtPlayToneBrick", LegoNxtPlayToneBrick.class);
		xstream.alias("loopBeginBrick", LoopBeginBrick.class);
		xstream.alias("loopEndBrick", LoopEndBrick.class);
		xstream.alias("loopEndlessBrick", LoopEndlessBrick.class);
		xstream.alias("moveNStepsBrick", MoveNStepsBrick.class);
		xstream.alias("nextLookBrick", NextLookBrick.class);
		xstream.alias("noteBrick", NoteBrick.class);
		xstream.alias("placeAtBrick", PlaceAtBrick.class);
		xstream.alias("playSoundBrick", PlaySoundBrick.class);
		xstream.alias("pointInDirectionBrick", PointInDirectionBrick.class);
		xstream.alias("pointToBrick", PointToBrick.class);
		xstream.alias("repeatBrick", RepeatBrick.class);
		xstream.alias("setBrightnessBrick", SetBrightnessBrick.class);
		xstream.alias("setGhostEffectBrick", SetGhostEffectBrick.class);
		xstream.alias("setLookBrick", SetLookBrick.class);
		xstream.alias("setSizeToBrick", SetSizeToBrick.class);
		xstream.alias("setVariableBrick", SetVariableBrick.class);
		xstream.alias("setVolumeToBrick", SetVolumeToBrick.class);
		xstream.alias("setXBrick", SetXBrick.class);
		xstream.alias("setYBrick", SetYBrick.class);
		xstream.alias("showBrick", ShowBrick.class);
		xstream.alias("speakBrick", SpeakBrick.class);
		xstream.alias("stopAllSoundsBrick", StopAllSoundsBrick.class);
		xstream.alias("turnLeftBrick", TurnLeftBrick.class);
		xstream.alias("turnRightBrick", TurnRightBrick.class);
		xstream.alias("waitBrick", WaitBrick.class);
		xstream.alias("whenBrick", WhenBrick.class);
		xstream.alias("whenStartedBrick", WhenStartedBrick.class);

		xstream.alias("dronePlayLedAnimationBrick", DronePlayLedAnimationBrick.class);
		xstream.alias("droneFlipBrick", DroneFlipBrick.class);
		xstream.alias("droneTakeOffBrick", DroneTakeOffBrick.class);
		xstream.alias("droneLandBrick", DroneLandBrick.class);
		xstream.alias("droneMoveForwardBrick", DroneMoveForwardBrick.class);
		xstream.alias("droneMoveBackwardBrick", DroneMoveBackwardBrick.class);
		xstream.alias("droneMoveUpBrick", DroneMoveUpBrick.class);
		xstream.alias("droneMoveDownBrick", DroneMoveDownBrick.class);
		xstream.alias("droneMoveLeftBrick", DroneMoveLeftBrick.class);
		xstream.alias("droneMoveRightBrick", DroneMoveRightBrick.class);
	}

	public File getBackPackSoundDirectory() {
		return backPackSoundDirectory;
	}

	public void clearBackPackSoundDirectory() {
		if (backPackSoundDirectory.listFiles().length > 1) {
			for (File node : backPackSoundDirectory.listFiles()) {
				if (!(node.getName().equals(".nomedia"))) {
					node.delete();
				}
			}
		}
	}

	public String getXMLStringOfAProject(Project project) {
		return xstream.toXML(project);
	}

}
