import json
import re
import time
import argparse
from pprint import pprint
from sys import stderr
from typing import Any


# header_reg = r"insert into \[?(\w+)\]?\n +\((\w+), ?(\w+),? ?(\w+)?\)"
header_reg = r"insert into \[?(\w+)\]?\n"
column_block_reg = r" {0,}?\(([\w ,_]+)\)\n? {0,}values\n?"
column_reg = r"(\w+),? ?"
entity_block_reg = r" {0,}\((.+)+\) {0,},?\n?"
entity_column_delimiter_reg = r",\s+(?=(?:(?:[^']*'){2})*[^']*$)"
entity_column_reg = r"'?([^'\n]+)'?"


def init_parser():
    parser = argparse.ArgumentParser(description='Process ddl to json')
    parser.add_argument('input_file', type=argparse.FileType('r'), help="path to input file")
    parser.add_argument('output_file', type=argparse.FileType('w+'), help="path to output file")
    parser.add_argument('-P', '--print', action='store_true')
    return parser.parse_args()

def log_error(section: str, body: str):
    print(f"{'='*10}{section: <14} error{'='*10}", file=stderr)
    print(body)
    print(f"{'='*10}/{section: <13} error{'='*10}", file=stderr)
    raise ValueError(body)

# PARSING CHAIN BEGIN (largest to smallest)

def read_parse_file(file_name: str):
    with open(file_name) as f:
        return parse_ddl_string(f.read())


def parse_ddl_string(contents: str):
    print(type(contents))
    inserts = [insert for insert in re.split("go;", contents, flags=re.IGNORECASE) if insert]
    ix: int = 0
    parsed_inserts = []
    if inserts:
        for ix, insert in enumerate(inserts):
            tic: float = time.perf_counter()
            parsed_inserts.append(insert_parse(insert))
            toc: float = time.perf_counter()
            print(f"Parsed {ix} of {len(inserts)} in {toc-tic:0.4f}", end="\n")
    return parsed_inserts


def insert_parse(insert: str) -> dict[str, str | list[dict[str, str]]]:
    class_name, header_end_ix = header_parse(insert)
    columns, columns_end_ix = columns_parse(insert[header_end_ix:])
    entities = entity_block_parse(insert[header_end_ix+columns_end_ix:])
    return {
        "endpoint": class_name,
        "body": [dict(zip(columns, entity)) for entity in entities]
    }


def header_parse(insert: str) -> tuple[str,int]:
    matches = re.search(header_reg, insert, flags=re.MULTILINE)
    if not matches:
        log_error("header", insert)
    else:
        return matches.group(1), matches.end()


def columns_parse(insert: str):
    column_block = re.search(column_block_reg, insert, flags=re.MULTILINE)
    if column_block:
        unparsed_columns: list[Any] = re.findall(column_reg, column_block.group(1), flags=re.MULTILINE)
        columns: list[str] = [column for column in unparsed_columns if column]
        if not columns:
            log_error("columns", insert)
        else:
            return columns, column_block.end()
    else:
        log_error("columns", insert)


def entity_block_parse(entity_blocks_str: str):
    entities = []
    entity_blocks: list[str]= entity_blocks_str.split('\n')
    for ix, entity_block in enumerate(entity_blocks):
        if entity_block:
            tic: float = time.perf_counter()
            entities.append(entity_parse(entity_block))
            toc: float = time.perf_counter()
            print(f"Entity {ix} of {len(entity_blocks)} parsed in {toc-tic:0.8f} ({entities[-1][-5:]})", end="\n")
    return entities


def entity_parse(entity_block: str):
    clean_block = re.search(entity_block_reg, entity_block, flags=re.MULTILINE)
    if clean_block:
        unparsed_columns: list[str | Any] = re.split(entity_column_delimiter_reg, clean_block.group(1))
        if unparsed_columns:
            return [
                col_match.group(1)
                    if (col_match:=re.search(entity_column_reg, column)) 
                    else log_error("entity", entity_block) 
                for column in unparsed_columns
            ]
        else:
            log_error("entities", entity_block)
    else:
        log_error("entities", entity_block)


if __name__ == '__main__':
    args = init_parser()
    data = parse_ddl_string(args.input_file.read())
    args.output_file.write(json.dumps(data, indent=2))
    if args.print: 
        pprint(data)
