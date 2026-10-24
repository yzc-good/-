const fs = require('fs');
const c = fs.readFileSync(process.argv[2], 'utf8');
const start = c.lastIndexOf('<script>');
const end = c.lastIndexOf('</script>');
let js = c.slice(start + '<script>'.length, end);
js = js.replace('/*__DATA__*/', '');
try {
  new Function('window', js);
  console.log('JS OK, length=' + js.length);
} catch (e) {
  console.log('JS ERROR: ' + e.message);
}