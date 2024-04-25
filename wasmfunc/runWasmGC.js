"use strict";
// USE WITH: deno run -A --v8-flags=--experimental-wasm-stringref runWasmGC.js <filename> <function-name> <args>

(async () => {
  const file = await Deno.readFile(Deno.args[0]);
  const wasm = await WebAssembly.compile(file);
  const exports = WebAssembly.Module.exports(wasm);

  const { instance } = await WebAssembly.instantiate(file, {});

  const funcName = Deno.args[1];
  const funcArgs = Deno.args.slice(2);
  const funcExists = exports.some(
    (exp) => exp.kind === "function" && exp.name === funcName
  );

  if (!funcExists) {
    throw new Error(`Wasm func ${funcName} does not exist in ${Deno.args[0]}`);
  }

  const output = instance.exports[funcName](...funcArgs);

  console.log(Number(output));
})();
