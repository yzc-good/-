
vector 是 C++ STL 中最常用、最核心的序列式容器，本质是动态大小的数组（也叫 “动态数组”）。它既保留了原生数组 “随机访问高效” 的优点，又解决了原生数组 “大小固定、无法动态扩展” 的问题，是日常开发中处理一组同类型数据的首选

二、vector 的基础使用（必备语法）
1. 前置条件
使用 vector 必须包含头文件，且建议使用 std 命名空间（或显式写 std::vector）：
cpp
运行
#include <vector>   // 核心头文件
#include <iostream> // 用于输出（示例用）
using namespace std; // 简化代码，否则需写 std::vector
2. 定义与初始化
vector 是模板类，定义时需指定元素类型（如 int、string、自定义类），常见初始化方式如下：
cpp
运行
// 方式1：空vector（最常用，后续动态添加元素）
vector<int> vec1;

// 方式2：初始化时指定大小，元素默认值为0（int）/空字符串（string）
vector<int> vec2(5); // 5个int元素，值都是0
vector<string> vec3(3); // 3个string元素，值都是空字符串

// 方式3：指定大小+初始值
vector<int> vec4(5, 10); // 5个int元素，值都是10

// 方式4：用列表初始化（C++11及以上）
vector<int> vec5 = {1, 2, 3, 4, 5};
vector<int> vec6{1, 2, 3}; // 等价于上面，可省略=

// 方式5：拷贝初始化（用另一个vector初始化）
vector<int> vec7(vec5); // vec7和vec5内容完全一样
3. 核心操作（增删改查）
这是 vector 最常用的功能，按 “增、删、改、查” 分类讲解：
（1）增加元素
表格
方法	作用	示例
push_back(值)	尾部添加元素（最常用）	vec.push_back(6);
emplace_back(值)	C++11 新增，尾部构造元素（更高效）	vec.emplace_back(7);
insert(迭代器, 值)	在指定位置插入元素（低效）	vec.insert(vec.begin()+2, 9); // 在索引 2 处插入 9
示例：
cpp
运行
vector<int> vec;
vec.push_back(1);  // vec: [1]
vec.push_back(2);  // vec: [1,2]
vec.emplace_back(3); // vec: [1,2,3]（效率比push_back高）
vec.insert(vec.begin()+1, 10); // vec: [1,10,2,3]（在索引1处插10）
（2）删除元素
表格
方法	作用	示例
pop_back()	删除尾部元素（最常用）	vec.pop_back();
erase(迭代器)	删除指定位置元素	vec.erase(vec.begin()+1);
erase(迭代器1, 迭代器2)	删除区间内元素（左闭右开）	vec.erase(vec.begin(), vec.begin()+2);
clear()	清空所有元素（容器大小变为 0）	vec.clear();
示例：
cpp
运行
vector<int> vec = {1,10,2,3};
vec.pop_back();     // vec: [1,10,2]（删除尾部3）
vec.erase(vec.begin()+1); // vec: [1,2]（删除索引1的10）
vec.clear();        // vec: []（空容器）
（3）修改元素
vector 支持两种修改方式：下标 [] 或迭代器，核心是 “随机访问”：
cpp
运行
vector<int> vec = {1,2,3};
vec[0] = 10;        // 下标修改：第一个元素改为10 → [10,2,3]
vec.at(1) = 20;     // at()修改（带越界检查，更安全）→ [10,20,3]

// 迭代器修改
auto it = vec.begin() + 2;
*it = 30;           // 第三个元素改为30 → [10,20,30]
⚠️ 注意：[ ]不做越界检查（越界会崩溃），at() 会做越界检查（越界抛异常），新手推荐用 at()。
（4）查询 / 访问元素
表格
方法	作用	示例
vec[index]	访问索引 index 的元素（无越界检查）	cout << vec[0];
vec.at(index)	访问索引 index 的元素（有越界检查）	cout << vec.at(0);
vec.front()	访问第一个元素	cout << vec.front();
vec.back()	访问最后一个元素	cout << vec.back();
vec.begin()/vec.end()	返回迭代器（遍历用）	见下文遍历示例
三、vector 的遍历方式（4 种常用）
遍历是使用 vector 的高频操作，推荐按 “简洁度” 优先级选择：
1. 范围 for 循环（C++11+，最简洁）
cpp
运行
vector<int> vec = {10,20,30};
for (int num : vec) {       // 遍历每个元素，num是拷贝
    cout << num << " ";     // 输出：10 20 30
}
// 优化：用const&避免拷贝（大数据更高效）
for (const int& num : vec) {
    cout << num << " ";
}
// 如需修改元素：用&引用
for (int& num : vec) {
    num *= 2; // 每个元素乘2 → vec变为[20,40,60]
}
2. 普通下标循环（和数组一致，新手易理解）
cpp
运行
vector<int> vec = {10,20,30};
for (int i = 0; i < vec.size(); ++i) { // size()返回元素个数
    cout << vec[i] << " "; // 输出：10 20 30
}
3. 迭代器循环（通用，适配所有 STL 容器）
cpp
运行
vector<int> vec = {10,20,30};
// 普通迭代器（可修改元素）
for (vector<int>::iterator it = vec.begin(); it != vec.end(); ++it) {
    cout << *it << " "; // *it解引用获取元素值
}
// 只读迭代器（更安全，不能修改元素）
for (vector<int>::const_iterator it = vec.cbegin(); it != vec.cend(); ++it) {
    cout << *it << " ";
}
// C++11+ 简化迭代器定义（auto自动推导类型）
for (auto it = vec.cbegin(); it != vec.cend(); ++it) {
    cout << *it << " ";
}
4. for_each 算法（STL 算法，适合自定义复杂操作）
cpp
运行
#include <algorithm> // 需包含算法头文件
vector<int> vec = {10,20,30};
// 遍历并执行lambda表达式（输出元素）
for_each(vec.begin(), vec.end(), [](int num) {
    cout << num << " ";
});
四、vector 的常用属性 / 方法
除了增删改查，这些方法能帮你管理和了解 vector：
表格
方法	作用	示例
vec.size()	返回当前元素个数（最常用）	cout << vec.size();
vec.empty()	判断是否为空（返回 bool）	if (vec.empty()) { ... }
vec.capacity()	返回当前容量（已分配的内存能存多少元素）	cout << vec.capacity();
vec.reserve(n)	预分配 n 个元素的容量（避免频繁扩容）	vec.reserve(100);
vec.resize(n)	调整容器大小为 n，不足补默认值0，超出删除	vec.resize(5);
⚠️ 关键区别：size() 是实际元素个数，capacity() 是已分配的内存能容纳的元素数。比如：
cpp
运行
vector<int> vec;
vec.push_back(1);
cout << vec.size();    // 输出1（1个元素）
cout << vec.capacity();// 输出4（不同编译器默认扩容策略不同，通常初始容量4）
reserve(n) 是性能优化技巧：如果提前知道要存 1000 个元素，先 vec.reserve(1000)，避免多次扩容的拷贝开销。
//-----------------------------------------------------------------------------
#include <iostream>
#include <vector>
using namespace std;

int main()
{
    vector<int> vec1;
    vec1.reserve(100);
    for (int i = 0; i < 10; i++)
    {
        int temp;
        cin >> temp;
        vec1.push_back(temp);
    }
    for (int num : vec1) {
        cout << num << ' ';
    }
    return 0;
}
//-----------------------------------------------------------------------------
