function every<T>(itr: Iterable<T>, pre: (e: T) => boolean): boolean {
	for(const e of itr) if(!pre(e)) return false;
	return true;
}

function some<T>(itr: Iterable<T>, pre: (e: T) => boolean): boolean {
	for(const e of itr) if(pre(e)) return true;
	return false;
}

function maketrans(src: string, tgt: string): (c: string) => string {
	// TODO improve efficiency
	return (chr: string) => {
		const pos = src.indexOf(chr);
		if(pos < 0) {
			return chr;
		} else return tgt[pos];
	};
}

function translate(val: string, tr: (c: string) => string) {
	const chars: string[] = [];
	for(const c of val) {
		chars.push(tr(c));
	}
	return chars.join("");
}

function parseHtml(text: string): Node[] {
	const parent = document.createElement("div");
	parent.innerHTML = text;
	return Array.from(parent.childNodes);
}

const hira = "ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをんゔゕゖゝゞ";
const kata = "ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶヽヾ";
const to_hira_tbl = maketrans(kata, hira);
const to_kata_tbl = maketrans(hira, kata);
const non_script_chrs = "ー・";
const is_hira_set = new Set(hira + non_script_chrs);
const is_kata_set = new Set(kata + non_script_chrs);

function is_hira(kana: string): boolean {
	return every(kana, c => is_hira_set.has(c));
}

function to_hira(kana: string): string {
	return translate(kana, to_hira_tbl);
}

function is_kata(kana: string): boolean {
	return every(kana, (c) => is_kata_set.has(c));
}

function to_kata(kana: string): string {
	return translate(kana, to_kata_tbl);
}

function comp_kana(kana: string, ...args: string[]): boolean {
	const first = to_kata(kana);
	return every(args, kstr => to_kata(kstr) === first);
}

const i_dan = ["キ", "ギ", "シ", "ジ", "チ", "ヂ", "ニ", "ヒ", "ビ", "ピ", "ミ", "リ"];
const e_comp = ["イ", "ウ", "キ", "ギ", "ク", "グ", "シ", "ジ", "チ", "ツ", "ニ", "ヒ", "ビ", "ピ", "フ", "ミ", "リ", "ヴ"];

function split_moras(reading: string, as_hira: boolean = false): string[] {
	const conv_fn = as_hira ? to_hira : to_kata;
	const kana = to_kata(reading);
	const moras: string[] = [];
	for(let i = 0; i < kana.length; ++i) {
		const ck = kana[i];
		const nk = i + 1 < kana.length ? kana[i + 1] : null;
		if(nk !== null) {
			if(i_dan.includes(ck) && ["ャ", "ュ", "ョ"].includes(nk)
				|| nk === "ヮ" && ["ク", "グ"].includes(ck)
				|| nk === "ァ" && ["ツ", "フ", "ヴ"].includes(ck)
				|| nk === "ィ" && ["ク", "グ", "ス", "ズ", "テ", "ツ", "デ", "フ", "イ", "ウ", "ヴ"].includes(ck)
				|| nk === "ゥ" && ["ト", "ド", "ホ", "ウ"].includes(ck)
				|| nk === "ェ" && e_comp.includes(ck)
				|| nk === "ォ" && ["ク", "グ", "ツ", "フ", "ウ", "ヴ"].includes(ck)
				|| nk === "ャ" && ["フ", "ヴ"].includes(ck)
				|| nk === "ュ" && ["テ", "デ", "フ", "ウ", "ヴ"].includes(ck)
				|| nk === "ョ" && ["フ", "ヴ"].includes(ck)) {
				moras.push(conv_fn(ck + nk));
				++i;
				continue;
			}
		}
		moras.push(conv_fn(ck));
	}
	return moras;
}

function generate_accent_nodes(reading: string, accents: number[], is_yougen: boolean): [string, Node, Node] {
	function acc_span(text: string, flat: boolean = false): Node {
		const span = document.createElement("span");
		span.classList.add(flat ? "jrp-graph-bar-unaccented" : "jrp-graph-bar-accented");
		span.append(text);
		return span;
	}

	function pattern_class(acc: number, mora_count: number, is_yougen: boolean): string {
		if(acc == 0) {
			return "jrp-heiban";
		} else if(is_yougen) {
			return "jrp-kifuku";
		} else if(acc == 1) {
			return "jrp-atamadaka";
		} else if(acc == mora_count) {
			return "jrp-odaka";
		} else {
			return "jrp-nakadaka";
		}
	}

	const moras = split_moras(reading);
	const graph_div = document.createElement("div");
	graph_div.classList.add("jrp-graph");

	const indicator_div = document.createElement("div");
	indicator_div.classList.add("jrp-indicator-container");

	function mora_slice(start: number, end?: number): string {
		return moras.slice(start, end).join("");
	}

	let first_pat: string | null = null;
	for(const acc of accents) {
		const pat_class = pattern_class(acc, moras.length, is_yougen);
		if(first_pat === null) {
			first_pat = pat_class;
		}

		const acc_div = document.createElement("div");
		acc_div.classList.add(pat_class);
		if(acc === 1) {
			acc_div.append(acc_span(moras[0]), mora_slice(1));
		} else if(acc === 0) {
			acc_div.append(moras[0], acc_span(mora_slice(1), true));
		} else {
			acc_div.append(moras[0], acc_span(mora_slice(1, acc)), mora_slice(acc));
		}
		graph_div.appendChild(acc_div);

		const acc_indicator = document.createElement("div");
		acc_indicator.classList.add("jrp-indicator", pat_class);
		indicator_div.append(acc_indicator);
	}
	return [first_pat!, graph_div, indicator_div];
}

class Segment {
	constructor(public text: string, public reading: string | null = null) {
		if(reading !== null && reading.length > 0 && !comp_kana(text, reading)) {
			this.reading = reading;
		} else this.reading = null;
	}

	get_reading(): string {
		return (this.reading !== null ? this.reading : this.text);
	}
}

class Unit {
	constructor(
		public segments: Segment[],
		public accents: number[] = [],
		public is_yougen: boolean = false,
		public uncertain: boolean = false,
		public base_reading: string | null = null) {
	}

	reading(): string {
		if(this.base_reading === null) {
			return this.segments.map(s => s.get_reading()).join("");
		} else return this.base_reading;
	}

	generate_dom_node(): Node {
		const segment_nodes: Node[] = this.segments.flatMap(s => {
			if(s.reading === null) {
				return parseHtml(s.text);
			} else {
				const rt = document.createElement("rt");
				rt.append(...parseHtml(s.reading));

				const ruby = document.createElement("ruby");
				ruby.append(...parseHtml(s.text));
				ruby.appendChild(rt);
				return [ruby];
			}
		});

		const unit_span = document.createElement("span");
		unit_span.classList.add("jrp-unit");
		unit_span.append(...segment_nodes);

		if(this.accents.length > 0) {
			const [pat_class, graph, indicators] = generate_accent_nodes(this.reading(), this.accents, this.is_yougen);

			unit_span.classList.add(pat_class);
			unit_span.append(indicators, graph);
		}
		return unit_span;
	}
}

class ParsingError extends Error {
	constructor(msg: string) {
		super(msg);
	}
}

function read_until(val: string, idx: number, stop: string[]): [number, string | null, string] {
	// implementation differs from Python
	const chars: string[] = [];
	for(let i = idx; i < val.length; ++i) {
		const c = val[i];
		if(stop.includes(c)) {
			return [i, c, chars.join("")];
		} else if(c === "\\") {
			if(++i < val.length) {
				chars.push(val[i]);
			} else throw new ParsingError("backslash at end of input");
		} else chars.push(c);
	}
	return [val.length, null, chars.join("")];
}

function parse_migaku_accents(val: string, reading: string): number[] {
	function convert(tag: string, moras: number): number {
		switch(tag[0]) {
			case "h":
				return 0;
			case "a":
				return 1;
			case "k":
			case "n":
				return parseInt(tag.slice(1));
			case "o":
				return moras;
			default:
				throw new ParsingError(`invalid Migaku accent pattern: ${tag}`);
		}
	}

	const moras = split_moras(reading).length;
	const tags = val.split(",");
	return tags.map(t => convert(t, moras));
}

function parse_migaku(val: string): Unit[] {
	enum State {
		BASE_READING,
		ACCENTS,
		SUFFIX,
	}

	class Parser {
		private pos: number;

		constructor(private readonly val: string) {
			this.pos = 0;
		}

		skip_space() {
			while(this.pos < this.val.length && this.val[this.pos] === " ") {
				++this.pos;
			}
		}

		parse_unit(): Unit {
			let state: State;

			const [prfx_end, prfx_c, prefix] = read_until(this.val, this.pos, ["[", " "]);
			switch(prfx_c) {
				case " ":
				case null:
					this.pos = prfx_end + 1;
					return new Unit([new Segment(prefix)]);
				case "[":
					this.pos = prfx_end + 1;
					break;
			}

			const [rdng_end, rdng_c, prefix_reading] = read_until(this.val, this.pos, [",", ";", "]"]);
			switch(rdng_c) {
				case ",":
					state = State.BASE_READING;
					break;
				case ";":
					state = State.ACCENTS;
					break;
				case "]":
					state = State.SUFFIX;
					break;
				default:
					throw new ParsingError(`unclosed Migaku tag: ${this.val}`);
			}
			this.pos = rdng_end + 1;

			let base_reading: string = "";
			if(state === State.BASE_READING) {
				let bsfm_end: number, bsfm_c: string | null;
				[bsfm_end, bsfm_c, base_reading] = read_until(this.val, this.pos, [";", "]"]);
				switch(bsfm_c) {
					case ";":
						state = State.ACCENTS;
						break;
					case "]":
						state = State.SUFFIX;
						break;
					default:
						throw new ParsingError(`unclosed Migaku tag: ${this.val}`);
				}
				this.pos = bsfm_end + 1;
			}

			let accent_str: string = "";
			if(state === State.ACCENTS) {
				let acct_end: number, acct_c: string | null;
				[acct_end, acct_c, accent_str] = read_until(this.val, this.pos, ["]"]);
				switch(acct_c) {
					case "]":
						state = State.SUFFIX;
						break;
					default:
						throw new ParsingError(`closing ] missing: ${this.val}`);
				}
				this.pos = acct_end + 1;
			}

			let suffix: string = "";
			if(state === State.SUFFIX) {
				let sufx_end: number;
				[sufx_end, , suffix] = read_until(this.val, this.pos, [" "]);
				this.pos = sufx_end + 1;
			}

			// different from Python
			const segments = [new Segment(prefix, prefix_reading)];
			if(suffix.length > 0) {
				segments.push(new Segment(suffix));
			}
			const is_yougen = base_reading.length > 0;
			let accents: number[];
			if(accent_str.length > 0) {
				const reading = is_yougen ? base_reading : (prefix_reading + (suffix.length > 0 ? suffix : ""));
				accents = parse_migaku_accents(accent_str, reading);
			} else accents = [];
			return new Unit(segments, accents, is_yougen, false, is_yougen ? base_reading : null);
		}

		execute(): Unit[] {
			const units: Unit[] = [];
			while(this.pos < this.val.length) {
				this.skip_space();
				units.push(this.parse_unit());
			}
			return units;
		}
	}

	return new Parser(val).execute();
}

function parse_jrp(value: string): Unit[] {
	function parse_segment(val: string, start_idx: number): [number, Segment | [string, string]] {
		const [sep_idx, sep_c, seg_text] = read_until(val, start_idx + 1, ["|", "="]);
		if(sep_c !== null) {
			const [end_idx, end_c, reading] = read_until(val, sep_idx + 1, ["]"]);
			// different from Python
			if(end_c === null) {
				throw new ParsingError(`segment is missing closing bracket: ${val}`);
			}
			return [end_idx + 1, sep_c === "=" ? [seg_text, reading] : new Segment(seg_text, reading)];
		}
		throw new ParsingError(`invalid segment: ${val}`);
	}

	function parse_unit(val: string, start_idx: number): [number, Unit] {
		const segments: Segment[] = [];
		const base_reading_parts: string[] = [];

		let pos = start_idx + 1;
		let broke_out = false;
		while(pos < val.length) {
			let last_c: string | null, txt: string;
			[pos, last_c, txt] = read_until(val, pos, ["[", ";", "}"]);
			if(txt.length > 0) {
				segments.push(new Segment(txt));
				base_reading_parts.push(txt);
			}

			if(last_c === "[") {
				let srv: Segment | [string, string];
				[pos, srv] = parse_segment(val, pos);
				// different from Python
				if(srv instanceof Segment) {
					segments.push(srv);
					base_reading_parts.push(srv.get_reading());
				} else {
					const [text, base_reading] = srv;
					segments.push(new Segment(text));
					base_reading_parts.push(base_reading);
				}
			} else if(last_c === ";" || last_c === "}") {
				broke_out = true;
				break;
			}
		}
		if(!broke_out) {
			throw new ParsingError(`unclosed unit: ${val}`);
		}

		let accents: number[] = [];
		let special_base: string | null = null;
		let uncertain = false;
		let is_yougen = false;
		if(val[pos] === ";") {
			++pos;
			if(val[pos] === "!") {
				uncertain = true;
				++pos;
			}
			if(val[pos] === "Y") {
				is_yougen = true;
				++pos;
			}


			const [end_idx, end_c, accent_str] = read_until(val, pos, ["|", "}"]);
			if(end_c !== null) {
				// implementation differs from Python
				accents = accent_str.split(",").map(acc => {
					const val = parseInt(acc);
					if(isNaN(val)) {
						throw new ParsingError(`invalid accent: ${val}`);
					} else return val;
				});
			} else throw new ParsingError(`unclosed unit: ${val}`);

			if(end_c === "|") {
				let unit_end_idx: number, ec: string | null;
				[unit_end_idx, ec, special_base] = read_until(val, end_idx + 1, ["}"]);
				if(ec !== null) {
					pos = unit_end_idx;
				} else throw new ParsingError(`unclosed unit: ${val}`);
			} else {
				pos = end_idx;
			}
		}

		// different from Python
		let base_reading: string = base_reading_parts.join("");
		if(special_base !== null) {
			base_reading = special_base;
		}
		return [pos + 1, new Unit(segments, accents, is_yougen, uncertain, base_reading)];
	}

	const units: Unit[] = [];
	let free_segments: Segment[] = [];

	let idx = 0;
	while(idx < value.length) {
		let c: string | null, text: string;
		[idx, c, text] = read_until(value, idx, ["[", "{"]);
		if(text.length > 0) {
			free_segments.push(new Segment(text));
		}

		switch(c) {
			case "{":
				if(free_segments.length > 0) {
					units.push(new Unit(free_segments));
				}
				free_segments = [];
				let u: Unit;
				[idx, u] = parse_unit(value, idx);
				units.push(u);
				break;
			case "[":
				let segment: Segment | [string, string];
				[idx, segment] = parse_segment(value, idx);
				if(!(segment instanceof Segment)) {
					throw new ParsingError(`base form segment outside of unit: ${value}`);
				}
				free_segments.push(segment);
				break;
		}
	}

	if(free_segments.length > 0) {
		units.push(new Unit(free_segments));
	}

	return units;
}

function generator_settings(attr_val: string): object {
	const res = {};

	let idx = 0;
	while(idx < attr_val.length) {
		let stop_c: string | null, text: string;
		[idx, stop_c, text] = read_until(attr_val, idx, [";"]);
		const split = text.split(":");
		switch(split.length) {
			case 1:
				res[split[0]] = true;
				break;
			case 2:
				res[split[0]] = split[1];
				break;
			default:
				throw new ParsingError(`invalid config attribute: ${attr_val}`);
		}
	}
	return res;
}

function generate() {
	const root_elements: [Element, object][] = [];
	for(const e of document.querySelectorAll("[data-jrp-generate]")) {
		const settings = generator_settings(e.getAttribute("data-jrp-generate")!);
		if(e.parentElement!.closest("[data-jrp-generate]") === null) {
			let deepest_parent = e;
			while(deepest_parent.childNodes.length == 1 && deepest_parent.firstElementChild !== null) {
				deepest_parent = deepest_parent.firstElementChild;
			}
			root_elements.push([deepest_parent, settings]);
		}
	}

	const br_re = /<br[\t\n\f\r ]*>/;
	for(const [root, settings] of root_elements) {
		const lines = root.innerHTML.split(br_re);
		while(root.firstChild !== null) {
			root.firstChild.remove();
		}
		root.append(...lines.flatMap((line, index) => {
			const parser = "migaku" in settings ? parse_migaku : parse_jrp;
			const unit_nodes = parser(line).map(u => u.generate_dom_node());
			return index > 0 ? unit_nodes : [document.createElement("br"), ...unit_nodes];
		}));
		root.normalize();
	}
}

generate();
