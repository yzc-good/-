只要是对n个数进行满足某一要求的查询，就用哈希表

哈希表的核心价值是以近似 O (1) 的时间复杂度实现快速的插入、查找、删除操作，本质是通过哈希函数将「键（Key）」映射到数组的特定位置，从而跳过遍历，直接定位数据。

//--------------------------------------------------------------------------------------------------
#include <iostream>
#include <unordered_map>
#include <string>

using namespace std;

int main() {
    // 1. 定义哈希表：键为string（比如用户名），值为int（比如用户ID）
    unordered_map<string, int> userMap;

    // 2. 插入元素（三种常用方式）
    userMap["Alice"] = 1001;          // 方式1：直接赋值（不存在则插入，存在则覆盖）
    userMap.insert({"Bob", 1002});    // 方式2：insert插入（不存在则插入，存在则忽略）
    userMap.emplace("Charlie", 1003); // 方式3：emplace（直接构造，效率更高）

    // 3. 查找元素（两种方式）
    // 方式1：find() + 迭代器（推荐，避免键不存在时创建默认值）
    auto it = userMap.find("Alice");
    if (it != userMap.end()) { // 找到则迭代器指向该键值对，否则指向end()
        cout << "Alice的ID：" << it->second << endl; // it->first是键，it->second是值
    } else {
        cout << "未找到Alice" << endl;
    }

    // 方式2：[]访问（注意：键不存在时会自动插入，值为类型默认值，比如int=0）
    cout << "Bob的ID：" << userMap["Bob"] << endl;
    cout << "不存在的键默认值：" << userMap["Dave"] << endl; // 会插入{"Dave", 0}

    // 4. 遍历哈希表
    cout << "\n遍历所有键值对：" << endl;
    for (const auto& pair : userMap) {
        cout << "键：" << pair.first << "，值：" << pair.second << endl;
    }

    // 5. 删除元素
    userMap.erase("Dave"); // 删除指定键
    cout << "\n删除Dave后，元素数量：" << userMap.size() << endl;

    // 6. 清空哈希表
    userMap.clear();
    cout << "清空后是否为空：" << (userMap.empty() ? "是" : "否") << endl;

    return 0;
}
//----------------------------------------------------------------------------
#include <iostream>
#include <unordered_map>
#include <string>

using namespace std;

int main() {
    string s = "hello world";
    unordered_map<char, int> charCount;

    // 统计每个字符出现次数
    for (char c : s) {
        charCount[c]++; // 键不存在时，默认值为0，++后变为1
    }

    // 输出统计结果
    cout << "字符出现次数：" << endl;
    for (const auto& pair : charCount) {
        cout << "'" << pair.first << "'：" << pair.second << "次" << endl;
    }

    return 0;
}
