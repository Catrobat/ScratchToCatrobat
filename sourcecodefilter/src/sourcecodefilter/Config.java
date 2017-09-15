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

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.Map.Entry;
import java.util.regex.MatchResult;
import java.util.regex.Pattern;

public class Config {

	final private String patternString = "%\\{([A-Z]|[a-z]|[0-9]|_)+\\}";
	private Pattern regexPattern;
	private Map<String, Object> configMap;

	public Config(Map<String, Object> configMap) {
		this.configMap = configMap;
		this.regexPattern = Pattern.compile(patternString);
	}

	private String replacePlaceholders(final String entry) throws IOException {
		String newEntry = new String(entry);
		for (MatchResult match : Util.allMatches(regexPattern, entry)) {
			String placeholderString = match.group();
			String placeholderKey = placeholderString.replace("%{", "").replace("}", "");
			Object placeholderValueObject = configMap.get(placeholderKey);
			if (placeholderValueObject == null) {
				throw new IOException("Key '" + placeholderString + "' does not exist in "
                                      + "configuration file!");
			}
			String placeholderValue = placeholderValueObject.toString();
			newEntry = newEntry.replaceFirst(Pattern.quote(placeholderString), placeholderValue);
		}
		return newEntry;
	}

	public String getString(final String key) throws IOException {
		return replacePlaceholders(configMap.get(key).toString());
	}

	@SuppressWarnings("unchecked")
	public Set<String> getSet(final String key) throws IOException {
		HashSet<String> itemSet = new HashSet<>();
		for (String item : (ArrayList<String>)configMap.get(key)) {
			itemSet.add(replacePlaceholders(item));
		}
		return itemSet;
	}

	@SuppressWarnings("unchecked")
	public Map<String, Set<String>> getMap(String key) throws IOException {
		Map<String, Set<String>> itemsMap = new HashMap<>();
		for (Entry<String, ArrayList<String>> entry : ((Map<String, ArrayList<String>>)configMap.get(key)).entrySet()) {
			HashSet<String> itemSet = new HashSet<>();
			for (String item : entry.getValue()) {
				itemSet.add(replacePlaceholders(item));
			}
			itemsMap.put(entry.getKey(), itemSet);
		}
		return itemsMap;
	}

}
