class JrpSegment {
	text: string;
	reading: string | null;

	constructor(text: string, reading: string | null = null) {
		this.text = text;
		this.reading = reading !== null && !_jrp_kana.comp(text, reading) ? reading : null;
	}

	get_reading(): string {
		return (this.reading !== null ? this.reading : this.text);
	}
}

class JrpUnit {
	segments: JrpSegment[];
	accents: number[];
	is_yougen: boolean;
	uncertain: boolean;
	base_reading: string | null;

	constructor(segments: JrpSegment[],
				accents: number[] = [],
				is_yougen: boolean = false,
				uncertain: boolean = false,
				base_reading: string | null = null) {
		this.segments = segments;
		this.accents = accents;
		this.is_yougen = is_yougen;
		this.uncertain = uncertain;
		this.base_reading = base_reading;
	}
}

class JrpParsingError extends Error {
	constructor(msg: string) {
		super(msg);
	}
}

const _jrp_kana = function() {
	function comp(...args: string[]): boolean {
		return true;
	}

	function split_moras(kana: string): string[] {
		return [];
	}

	return {comp, split_moras};
}();

const _jrp_parse = function() {
	function read_until(val: string, idx: number, stop: string[]): [number, string | null, string] {
		// implementation differs from Python
		const chars: string[] = [];
		for(let i = idx; i < val.length; ++i) {
			const c = val[i];
			if(stop.includes(c)) {
				return [idx + i, c, chars.join()];
			} else if(c === "\\") {
				if(++i < val.length) {
					chars.push(val[i]);
				} else throw new JrpParsingError("backslash at end of input");
			} else chars.push(c);
		}
		return [val.length, null, chars.join()];
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
					throw new JrpParsingError(`invalid Migaku accent pattern: ${tag}`);
			}
		}

		const moras = _jrp_kana.split_moras(reading).length;
		const tags = val.split(",");
		return tags.map((t) => convert(t, moras));
	}


	function parse_migaku(val: string): JrpUnit[] {
		enum State {
			BASE_READING,
			ACCENTS,
			SUFFIX,
		}

		class Parser {
			val: string;
			pos: number;

			constructor(val: string) {
				this.val = val;
				this.pos = 0;
			}

			skip_space() {
				while(this.pos < this.val.length && this.val[this.pos] === " ") {
					++this.pos;
				}
			}

			parse_unit(): JrpUnit {
				let state: State;

				const [prfx_end, prfx_c, prefix] = read_until(this.val, this.pos, ["[", " "]);
				switch(prfx_c) {
					case " ":
					case null:
						this.pos = prfx_end + 1;
						return new JrpUnit([new JrpSegment(prefix)]);
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
						throw new JrpParsingError(`unclosed Migaku tag: ${this.val}`);
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
							throw new JrpParsingError(`unclosed Migaku tag: ${this.val}`);
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
							throw new JrpParsingError(`closing ] missing: ${this.val}`);
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
				const segments = [new JrpSegment(prefix, prefix_reading)];
				if(suffix.length > 0) {
					segments.push(new JrpSegment(suffix));
				}
				const is_yougen = base_reading.length > 0;
				let accents: number[];
				if(accent_str.length > 0) {
					const reading = base_reading.length > 0 ? base_reading : (prefix_reading + (suffix.length > 0 ? suffix : ""));
					accents = parse_migaku_accents(accent_str, reading);
				} else accents = [];
				return new JrpUnit(segments, accents, is_yougen, false, base_reading);
			}

			execute(): JrpUnit[] {
				const units: JrpUnit[] = [];
				while(this.pos < this.val.length) {
					this.skip_space();
					units.push(this.parse_unit());
				}
				return units;
			}
		}

		return new Parser(val).execute();
	}


	function parse_jrp(value: string): JrpUnit[] {
		function parse_segment(val: string, start_idx: number): [number, JrpSegment | [string, string]] {
			const [sep_idx, sep_c, seg_text] = read_until(val, start_idx + 1, ["|", "="]);
			if(sep_c !== null) {
				const [end_idx, end_c, reading] = read_until(val, sep_idx + 1, ["]"]);
				// different from Python
				if(end_c === null) {
					throw new JrpParsingError(`segment is missing closing bracket: ${val}`);
				}
				return [end_idx + 1, sep_c === "=" ? [seg_text, reading] : new JrpSegment(seg_text, reading)];
			}
			throw new JrpParsingError(`invalid segment: ${val}`);
		}

		function parse_unit(val: string, start_idx: number): [number, JrpUnit] {
			const segments: JrpSegment[] = [];
			const base_reading_parts: string[] = [];

			let pos = start_idx + 1;
			let broke_out = false;
			while(pos < val.length) {
				let last_c: string | null, txt: string;
				[pos, last_c, txt] = read_until(val, pos, ["[", ";", "}"]);
				if(txt.length > 0) {
					segments.push(new JrpSegment(txt));
				}

				if(last_c === "[") {
					let srv: JrpSegment | [string, string];
					[pos, srv] = parse_segment(val, pos);
					// different from Python
					if(srv instanceof JrpSegment) {
						segments.push(srv);
						base_reading_parts.push(srv.get_reading());
					} else {
						const [text, base_reading] = srv;
						segments.push(new JrpSegment(text));
						base_reading_parts.push(base_reading);
					}
				} else if(last_c === ";" || last_c === "}") {
					broke_out = true;
					break;
				}
			}
			if(!broke_out) {
				throw new JrpParsingError(`unclosed unit: ${val}`);
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
					accents = accent_str.split(",").map((acc) => {
						const val = parseInt(acc);
						if(isNaN(val)) {
							throw new JrpParsingError(`invalid accent: ${val}`);
						} else return val;
					});
				} else throw new JrpParsingError(`unclosed unit: ${val}`);

				if(end_c === "|") {
					let unit_end_idx: number, ec: string | null;
					[unit_end_idx, ec, special_base] = read_until(val, end_idx + 1, ["}"]);
					if(ec !== null) {
						pos = unit_end_idx;
					} else throw new JrpParsingError(`unclosed unit: ${val}`);
				} else {
					pos = end_idx;
				}
			}

			// different from Python
			const base_reading = is_yougen ? (special_base !== null ? special_base : base_reading_parts.join()) : null;
			return [pos + 1, new JrpUnit(segments, accents, is_yougen, uncertain, base_reading)];
		}

		const units: JrpUnit[] = [];
		let free_segments: JrpSegment[] = [];

		let idx = 0;
		while(idx < value.length) {
			let c: string | null, text: string;
			[idx, c, text] = read_until(value, idx, ["[", "{"]);
			if(text.length > 0) {
				free_segments.push(new JrpSegment(text));
			}

			switch(c) {
				case "{":
					if(free_segments.length > 0) {
						units.push(new JrpUnit(free_segments));
					}
					free_segments = [];
					let u: JrpUnit;
					[idx, u] = parse_unit(value, idx);
					units.push(u);
					break;
				case "[":
					let segment: JrpSegment | [string, string];
					[idx, segment] = parse_segment(value, idx);
					if(!(segment instanceof JrpSegment)) {
						throw new JrpParsingError(`base form segment outside of unit: ${value}`);
					}
					free_segments.push(segment);
					break;
			}
		}

		if(free_segments.length > 0) {
			units.push(new JrpUnit(free_segments));
		}

		return units;
	}

	return {parse_migaku, parse_jrp};
}();
