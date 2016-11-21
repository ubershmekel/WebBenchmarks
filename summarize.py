"""
Raw results data from
https://tfb-logs.techempower.com/

"""

import csv
import json
from collections import namedtuple
import pprint


ResultsType = namedtuple('results', 'name perf')


def first(view):
    for item in view:
        return item
    raise Exception("Empty view :(")


def get_pass_all_tests(results_json):
    good = set()
    for test_type_name, test_names in results_json["succeeded"].items():
        if len(good) == 0:
            good = set(test_names)
        else:
            good = good.intersection(test_names)
        print('Good: %d' % len(good))
    return good


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
    # latency = results_seq[0][latency_key]

    errors_key = "5xx"

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
        if errors_key in result and result[errors_key] > 0:
            # NOTE: This was surprising that there were frameworks failing it all here.
            return

        count = result[results_key]
        duration = result["endTime"] - result["startTime"]
        perf = count * 1.0 / duration
        perf_seq.append(perf)
        # if lang == 'C#':
        #    print(framework_name)
        #    print(perf)
        #    pass

    # return sum(perf_seq) * 1.0 / len(perf_seq)
    # return max(perf_seq)
    # Here comes my opinion - I give you points based on how good is the
    # benchmark you are the worst at.
    return min(perf_seq)


def combine_results_with_meta(results_json, name_to_metadata):
    test_type_to_language_perfs = {}
    for test_type_name, name_to_results in results_json["rawData"].items():
        if test_type_name in ('commitCounts', 'slocCounts'):
            continue
        best_per_lang = {}
        print(test_type_name)
        for framework_name, results in name_to_results.items():
            meta = name_to_metadata[framework_name]
            lang = meta['language']
            # if lang == 'PHP':
            #     print(1)
            requests_per_sec = get_perf(results_seq=results)
            if requests_per_sec is None:
                continue
            if lang in best_per_lang:
                previous_best = best_per_lang[lang]
                if requests_per_sec > previous_best.perf:
                    best_per_lang[lang] = ResultsType(framework_name, requests_per_sec)
            else:
                best_per_lang[lang] = ResultsType(name=framework_name, perf=requests_per_sec)

        # pprint.pprint(best_per_lang)
        test_type_to_language_perfs[test_type_name] = best_per_lang
    return test_type_to_language_perfs


def seq_to_html(sequence):
    rows_html = []
    header_row = sequence[0]
    line = '<thead><tr><th>' + '</th><th>'.join(header_row) + '</th></tr></thead>'
    rows_html.append(line)
    for row in sequence[1:]:
        line = '<tr><td>' + '</td><td>'.join(row) + '</td></tr>'
        rows_html.append(line)
    table_html = '\n'.join(rows_html)
    return table_html

def main():
    results_json = json.load(open('results.json'))
    test_metadata_json = json.load(open('test_metadata.json'))
    name_to_metadata = {}

    for test in test_metadata_json:
        name_to_metadata[test['name']] = test

    # results_json["concurrencyLevels"]

    test_type_to_language_perfs = combine_results_with_meta(
        results_json=results_json,
        name_to_metadata=name_to_metadata)

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

    # output csv
    csv_file = open('results.csv', 'w')
    sorted_test_types = sorted(test_type_to_language_perfs.keys())
    headers = ['Language'] + sorted_test_types + ['Minimum']
    writer = csv.writer(csv_file, lineterminator='\n')
    writer.writerow(headers)
    table = [headers]
    for lang, perfs in lang_to_results.items():
        row = [lang]
        performances = []
        for typ in sorted_test_types:
            if typ not in perfs:
                break
            col = int(perfs[typ].perf)
            performances.append(col)
        if len(performances) != len(sorted_test_types):
            print("Bad row for: %s" % lang)
            continue
        row = row + [str(i) for i in performances] + [str(min(performances))]
        table.append(row)
        writer.writerow(row)

    # output html
    table_html = seq_to_html(table)
    html = open('template.html').read()
    html_out = html.replace('REPLACE_TABLE_HTML', table_html)
    open('index.html', 'w').write(html_out)

if __name__ == "__main__":
    main()
