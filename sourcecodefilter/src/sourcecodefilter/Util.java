/*
 * ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
 * Copyright (C) 2013-2016 The Catrobat Team
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
import java.net.URL;
import java.nio.channels.Channels;
import java.nio.channels.ReadableByteChannel;
import java.util.Enumeration;
import java.util.Iterator;
import java.util.regex.MatchResult;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.NoSuchElementException;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

public class Util {

    /**
     * taken from http://stackoverflow.com/a/6020436
     * @param p
     * @param input
     * @return Iterable<MatchResult>
     */
    public static Iterable<MatchResult> allMatches(final Pattern p, final CharSequence input) {
    	return new Iterable<MatchResult>() {
    		public Iterator<MatchResult> iterator() {
    			return new Iterator<MatchResult>() {
    				// Use a matcher internally.
    				final Matcher matcher = p.matcher(input);
    				// Keep a match around that supports any interleaving of hasNext/next calls.
    				MatchResult pending;

    				public boolean hasNext() {
    					// Lazily fill pending, and avoid calling find() multiple times if the
    					// clients call hasNext() repeatedly before sampling via next().
    					if (pending == null && matcher.find()) {
    						pending = matcher.toMatchResult();
    					}
    					return pending != null;
    				}

    				public MatchResult next() {
    					// Fill pending if necessary (as when clients call next() without
    					// checking hasNext()), throw if not possible.
    					if (!hasNext()) { throw new NoSuchElementException(); }
    					// Consume pending so next call to hasNext() does a find().
    					MatchResult next = pending;
    					pending = null;
    					return next;
    				}

    				/** Required to satisfy the interface, but unsupported. */
    				public void remove() { throw new UnsupportedOperationException(); }
    			};
    		}
    	};
    }
    
    public static void close(Closeable closeable) {
    	if (closeable == null) return;
    	try { closeable.close(); } catch (IOException e) {}
    }

    public static void downloadFile(final URL url, File file) throws IOException {
        FileOutputStream fos = null;
        try {
        	fos = new FileOutputStream(file);
        	ReadableByteChannel rbc = Channels.newChannel(url.openStream());
        	fos.getChannel().transferFrom(rbc, 0, Long.MAX_VALUE);
        	Util.close(fos);
        } catch (IOException ex) {
			Util.close(fos);
			throw ex;
        }
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
