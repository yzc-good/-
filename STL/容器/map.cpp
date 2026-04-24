一、map/multimap 核心概念解析
map 和 multimap 是 C++ STL（标准模板库）中关联式容器的核心，本质是基于红黑树实现的有序键值对（key-value）容器，核心特点是「按 key 自动排序」，区别仅在于 key 是否允许重复。
1. 核心定义（通俗版）
•	键值对（key-value）：可以理解为「字典」—— key 是 “单词”（用于查找），value 是 “单词释义”（实际存储的数据）。
•	map：key 是唯一的（比如字典里一个单词只能有一个条目），按 key 升序排列（默认）。
•	multimap：key 可重复（比如同一个单词有多个不同释义），同样按 key 升序排列，重复的 key 会相邻存放。
2. 底层实现
两者均基于红黑树（一种自平衡二叉搜索树），因此：
•	查找、插入、删除的时间复杂度均为 O(logn)（效率远高于无序容器如 unordered_map）；
•	遍历容器时，结果天然按 key 有序；
•	不支持随机访问（不能用 [] 直接通过下标访问，map 是特例，下文会讲）。
二、map 详细使用
1. 基本用法（完整示例）
cpp
运行
#include <iostream>
#include <map>   // 必须包含头文件
#include <string>
using namespace std;

int main() {
    // 1. 定义map：键类型int，值类型string，默认按key升序排列
    map<int, string> student;

    // 2. 插入元素（三种常用方式）
    // 方式1：[] 运算符（最简洁，key不存在则插入，存在则修改value）
    student[101] = "张三";
    student[102] = "李四";
    student[101] = "张三_修改版";  // key=101已存在，覆盖value

    // 方式2：insert() 插入（推荐，避免误覆盖，返回插入结果）
    // pair<iterator, bool>：iterator指向插入/已存在的元素，bool表示是否插入成功
    auto ret1 = student.insert({103, "王五"});  // 插入成功，bool=true
    auto ret2 = student.insert({101, "张三_重复"}); // key已存在，插入失败，bool=false

    // 方式3：emplace() 插入（更高效，直接构造对象，避免拷贝）
    student.emplace(104, "赵六");

    // 3. 查找元素
    // find(key)：找到返回迭代器，未找到返回end()
    auto it = student.find(102);
    if (it != student.end()) {
        cout << "找到key=102：" << it->first << " " << it->second << endl;
    } else {
        cout << "未找到key=102" << endl;
    }

    // 4. 遍历元素（天然按key升序）
    cout << "\n遍历map：" << endl;
    for (const auto& p : student) {  // 推荐用const&，避免拷贝
        cout << "key=" << p.first << ", value=" << p.second << endl;
    }

    // 5. 删除元素
    student.erase(103);  // 按key删除
    // student.erase(it); // 按迭代器删除
    // student.clear();   // 清空所有元素

    // 6. 常用属性
    cout << "\nmap大小：" << student.size() << endl;
    cout << "是否为空：" << (student.empty() ? "是" : "否") << endl;

    return 0;
}
2. 关键说明
•	[] 运算符的特殊性：map 支持 map[key]，但 multimap 不支持（因为 key 可重复，无法确定返回哪个 value）。
o	如果 key 存在，返回对应 value 的引用；
o	如果 key 不存在，会自动插入一个 key 为该值、value 为默认值（如 int 是 0，string 是空串）的键值对。
•	insert() vs emplace()：emplace () 直接在容器内构造对象，比 insert ()（先构造临时对象再拷贝）更高效，优先使用。
三、multimap 详细使用
1. 基本用法（完整示例）
cpp
运行
#include <iostream>
#include <map>
#include <string>
using namespace std;

int main() {
    // 1. 定义multimap：键int，值string，key可重复
    multimap<int, string> course;

    // 2. 插入元素（只能用insert/emplace，无[]运算符）
    course.insert({1001, "数学"});
    course.insert({1001, "高等数学"});  // key重复，允许插入
    course.emplace(1002, "英语");
    course.emplace(1001, "线性代数");  // 第三个key=1001的元素

    // 3. 查找元素（find()返回第一个匹配key的迭代器）
    auto it = course.find(1001);
    if (it != course.end()) {
        cout << "第一个key=1001：" << it->first << " " << it->second << endl;
    }

    // 4. 查找所有重复key的元素（equal_range()）
    cout << "\n所有key=1001的课程：" << endl;
    // equal_range返回pair<iterator, iterator>，表示重复key的范围
    auto range = course.equal_range(1001);
    for (auto i = range.first; i != range.second; ++i) {
        cout << i->first << " " << i->second << endl;
    }

    // 5. 遍历元素（按key升序，重复key相邻）
    cout << "\n遍历multimap：" << endl;
    for (const auto& p : course) {
        cout << "key=" << p.first << ", value=" << p.second << endl;
    }

    // 6. 删除元素（注意：erase(key)会删除所有该key的元素）
    int del_count = course.erase(1001);  // 返回删除的元素个数（此处是3）
    cout << "\n删除key=1001的元素个数：" << del_count << endl;

    return 0;
}
2. 关键说明
•	无 [] 运算符：因为 key 可重复，无法确定 multimap[key] 对应哪个 value，因此禁用 []。
•	equal_range()：multimap 核心函数，返回一个迭代器对，第一个迭代器指向第一个匹配 key 的元素，第二个指向最后一个匹配 key 的下一个位置，用于遍历所有重复 key 的元素。
•	erase(key)：会删除所有 key 匹配的元素，若只想删除其中一个，需先找到对应迭代器再删除（如 course.erase(it)）。
四、map vs multimap 核心对比
表格
特性	map	multimap
key 唯一性	唯一	可重复
[] 运算符	支持	不支持
insert () 结果	返回是否插入成功	始终插入成功
erase(key)	删除 1 个元素	删除所有匹配 key 的元素
适用场景	一对一映射（如 ID - 姓名）	一对多映射（如课程号 - 课程名）
总结
1.	map/multimap 是基于红黑树的有序键值对容器，天然按 key 升序排列，查找 / 插入 / 删除效率为 O(logn)；
2.	map 核心是「key 唯一」，支持 [] 运算符，适合一对一映射；
3.	multimap 核心是「key 可重复」，无 [] 运算符，需用 equal_range() 遍历重复 key，适合一对多映射。

