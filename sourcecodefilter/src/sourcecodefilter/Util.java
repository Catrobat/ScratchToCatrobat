/*
 * ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
 * Copyright (C) 2013-2015 The Catrobat Team
 * (http://developer.catrobat.org/credits)
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of the
 * License, or (at your option) any later version.
 *
 * An additional term exception under section 7 of the GNU Affero
 * General Public License, version 3, is available at
 * http://developer.catrobat.org/license_additional_term
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see http://www.gnu.org/licenses/.
 */

package sourcecodefilter;

import java.io.Closeable;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.Map.Entry;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

public class Util {

    @SuppressWarnings("unchecked")
    public static ArrayList<String> getListFromConfigForKey(String key, Map<String, Object> config) {
    	return (ArrayList<String>)config.get(key);
    }
	@SuppressWarnings("unchecked")
	public static Map<String, ArrayList<String>> getMapFromConfigForKey(String key, Map<String, Object> config) {
    	return (Map<String, ArrayList<String>>)config.get(key);
    }

    public static Map<String, Set<String>> convertArrayListToSetMapping(Map<String, ArrayList<String>> arrayListMapping) {
    	Map<String, Set<String>> setMapping = new HashMap<String, Set<String>>();
    	for (Entry<String, ArrayList<String>> entry : arrayListMapping.entrySet()){
    		setMapping.put(entry.getKey(), new HashSet<String>(entry.getValue()));
    	}
    	return setMapping;
    }

    public static void close(Closeable closeable) {
    	if (closeable == null) return;
    	try { closeable.close(); } catch (IOException e) {}
    }

    /**
     * taken from http://www.avajava.com/tutorials/lessons/how-do-i-unzip-the-contents-of-a-zip-file.html
     * @param zipArchive
     * @param outputDir
     * @return root directory path
     */
    public static String extractZip(File zipArchive, String outputDir) {
		try {
			String rootDirectoryPath = null;
			ZipFile zipFile = new ZipFile(zipArchive);
			Enumeration<?> enu = zipFile.entries();
			while (enu.hasMoreElements()) {
				ZipEntry zipEntry = (ZipEntry) enu.nextElement();
				String name = zipEntry.getName();
				long size = zipEntry.getSize();
				long compressedSize = zipEntry.getCompressedSize();
				System.out.printf("name: %-20s | size: %6d | compressed size: %6d\n", 
						name.substring(0, name.indexOf('/')), size, compressedSize);
				if (rootDirectoryPath == null) {
					rootDirectoryPath = name.substring(0, name.indexOf('/'));
				}
				File file = new File(outputDir, name);
				if (name.endsWith("/")) {
					file.mkdirs();
					continue;
				}
				File parent = file.getParentFile();
				if (parent != null) {
					parent.mkdirs();
				}
				InputStream is = zipFile.getInputStream(zipEntry);
				FileOutputStream fos = new FileOutputStream(file);
				byte[] bytes = new byte[1024];
				int length;
				while ((length = is.read(bytes)) >= 0) {
					fos.write(bytes, 0, length);
				}
				is.close();
				fos.close();
			}
			zipFile.close();
			return rootDirectoryPath;
		} catch (IOException e) {
			e.printStackTrace();
			return null;
		}
    }

    public static boolean deleteDirectory(File directory) {
    	if (directory.exists()) {
    		File[] files = directory.listFiles();
    		if (null != files) {
    			for (int i = 0; i < files.length; ++i) {
    				if (files[i].isDirectory()) {
    					deleteDirectory(files[i]);
    				} else {
    					files[i].delete();
    				}
    			}
    		}
    	}
    	return(directory.delete());
    }

}
