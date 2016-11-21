"""
Raw results data from
https://tfb-logs.techempower.com/

"""

import csv
import json
from collections import namedtuple
import pprint

def first(view):
    for item in view:
        return item
    raise Exception("Empty view :(")

ResultsType = namedtuple('results', 'name perf')



def get_pass_all_tests(results_json):
    good = set()
    for test_type_name, test_names in results_json["succeeded"].items():
        if len(good) == 0:
            good = set(test_names)
        else:
            good = good.intersection(test_names)
        print('Good: %d' % len(good))
    return good()

def get_perf(results_seq):
    # if framework_name not in good:
    #    continue
    # print(name)
    latency_key = 'latencyAvg'
    if type(results_seq) == int:
        # commitCounts and slocCounts
        # print('what')
        return
    if latency_key not in results_seq[0]:
        return
    latency = results_seq[0][latency_key]
    # print(name, lang, latency)

    # "totalRequests": 128606,
    # "startTime": 1478923715,
    # "endTime": 1478923730
    results_key = "totalRequests"
    perf_seq = []
    for result in results_seq:
        # each result is for a different concurrency level
        if results_key not in result:
            return
        count = result[results_key]
        duration = result["endTime"] - result["startTime"]
        perf = count * 1.0 / duration
        perf_seq.append(perf)
        # if lang == 'C#':
        #    print(framework_name)
        #    print(perf)
        #    pass

    #return sum(perf_seq) * 1.0 / len(perf_seq)
    return max(perf_seq)


def main():
    results_json = json.load(open('results.json'))
    test_metadata_json = json.load(open('test_metadata.json'))
    name_to_metadata = {}

    for test in test_metadata_json:
        name_to_metadata[test['name']] = test

    test_type_to_language_perfs = {}
    for test_type_name, name_to_results in results_json["rawData"].items():
        if test_type_name in ('commitCounts', 'slocCounts'):
            continue
        best_per_lang = {}
        print(test_type_name)
        for framework_name, results in name_to_results.items():
            avg_requests_per_sec = get_perf(results_seq=results)
            if avg_requests_per_sec is None:
                continue
            meta = name_to_metadata[framework_name]
            lang = meta['language']
            if lang in best_per_lang:
                previous_best = best_per_lang[lang]
                if avg_requests_per_sec > previous_best.perf:
                    best_per_lang[lang] = ResultsType(framework_name, avg_requests_per_sec)
            else:
                best_per_lang[lang] = ResultsType(name=framework_name, perf=avg_requests_per_sec)

        #pprint.pprint(best_per_lang)
        test_type_to_language_perfs[test_type_name] = best_per_lang

    pprint.pprint(test_type_to_language_perfs)

    # normalize to 100% instead of requests per second
    normalized = {}
    for test_type_name, perfs in test_type_to_language_perfs.items():
        normalized[test_type_name] = {}
        fastest_speed = max(langperf.perf for langperf in perfs.values())
        for lang, langperf in perfs.items():
            normperf = langperf.perf * 100.0 / fastest_speed
            normalized[test_type_name][lang] = ResultsType(name=langperf.name, perf=normperf)


    test_type_to_language_perfs = normalized

    # Convert from a TestType key to a Lang key
    lang_to_results = {}
    for lang in first(test_type_to_language_perfs.values()):
        lang_to_results[lang] = {}
        for test_type_name, lang_to_perf in test_type_to_language_perfs.items():
            if lang not in lang_to_perf:
                continue
            lang_to_results[lang][test_type_name] = lang_to_perf[lang]


    csv_file = open('results.csv', 'w')
    sorted_test_types = sorted(test_type_to_language_perfs.keys())
    headers = ['Language'] + sorted_test_types
    writer = csv.writer(csv_file, lineterminator='\n')
    writer.writerow(headers)
    for lang, perfs in lang_to_results.items():
        row = [lang]
        for typ in sorted_test_types:
            if typ not in perfs:
                break
            col = str(int(perfs[typ].perf))
            row.append(col)
        if len(row) != len(headers):
            print("Bad row for: %s" % lang)
            continue
        writer.writerow(row)

if __name__ == "__main__":
    main()