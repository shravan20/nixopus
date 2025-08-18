package tasks

import "strings"

func GetStringFromMap(m map[string]string) string {
	var result string
	for key, value := range m {
		result += key + "=" + value + " "
	}
	return result
}

func GetMapFromString(s string) map[string]string {
	result := make(map[string]string)
	pairs := strings.Split(s, " ")
	for _, pair := range pairs {
		if pair != "" {
			kv := strings.Split(pair, "=")
			if len(kv) == 2 {
				result[kv[0]] = kv[1]
			}
		}
	}
	return result
}
